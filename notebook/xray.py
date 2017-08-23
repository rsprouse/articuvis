import os, re
import pandas as pd
import scipy.io.wavfile

# These are functions that are specific to the xray data and go in a separate repo.
def walk_xray_datadir(datadir):
    '''Walk datadir and return a dict in which the keys are speakers and the
values are lists of their utterances.'''
    speakers = {}
    jwre = re.compile(r'(JW\d+)$')
    for root, dirnames, filenames in os.walk(datadir):
        m = jwre.search(root)
        if m:
            spkr = m.groups()[0]
            utterances = [
                f.replace('.txy', '') for f in filenames if f.endswith('.txy')
            ]
            speakers[spkr] = utterances
    return speakers

def load_xray_files(datadir, speaker, utterance, badval=1000000):
    '''Load files from xray database related to a speaker and utterance.
Return as DataFrames. Convert the time data to seconds and distance
measurements to mm. Also remove bad values (1000000).'''
    spkrpath = os.path.join(datadir, speaker)
    rate, au = scipy.io.wavfile.read(os.path.join(spkrpath, utterance + '.wav'))

    # Load the tongue data
    articfile = os.path.join(spkrpath, utterance + '.txy')
    coordcols = [
        'UL_x', 'UL_y', 'LL_x', 'LL_y', 'T1_x', 'T1_y', 'T2_x', 'T2_y',
        'T3_x', 'T3_y', 'T4_x', 'T4_y', 'MI_x', 'MI_y', 'MM_x', 'MM_y'
    ]
    articdf = pd.read_csv(
            articfile,
            sep='\t',
            na_values=badval,
            names=['sec'] + coordcols
    )
    articdf['sec'] *= 1e-6 # Convert to seconds

    # Load the palate data.
    palfile = os.path.join(spkrpath, 'PAL.DAT')
    paldf = pd.read_csv(palfile, sep='\s+', header=None, names=['x', 'y'])

    # Load the pharynx data.
    phafile = os.path.join(spkrpath, 'PHA.DAT')
    phadf = pd.read_csv(phafile, sep='\s+', header=None, names=['x', 'y'])

    landmarkdf = pd.concat([
        paldf.assign(landmark = pd.Series(['palate'] * len(paldf))),
        phadf.assign(landmark = pd.Series(['pharynx'] * len(phadf)))
    ])
    
    # Convert all coordinates to mm.
    articdf[coordcols] *= 1e-3
    landmarkdf.loc[:, ['x','y']] *= 1e-3

    # Calculate velocities for all coordinate columns and add as <coordinate>_vel columns.
    articdf = articdf.join(articdf[coordcols].diff(), rsuffix='_vel')
    
    return (rate, au, articdf, landmarkdf)

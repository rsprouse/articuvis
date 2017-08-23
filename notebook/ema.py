import os, re
import pandas as pd
import scipy.io.wavfile
import wavio

# These are functions that are specific to the EMA data and go in a separate repo.
def ecog_speakerdir_for_speaker(speaker):
    '''Convert speaker names like SN125 to speaker directories like 
Subject_125.'''
    m = re.search(r'(\d+)$', speaker)
    speakerdir = 'Subject_{}'.format(m.groups()[0])
    return speakerdir

def read_ecog_speaker_audio(basepath, speaker, dataname, rep):
    '''Read a UCSF EMA (ECOG) speaker audio file. Return sample rate and
audio data as a numpy array.
'''
    if rep is None or rep == '':
        rep = ''
    else:
        if not isinstance(rep, str):  # if rep is passed as an int
            rep = '_{:03d}'.format(rep)
        elif not rep.startswith('_'):
            rep = '_' + rep
    fname = os.path.join(
        basepath,
        ecog_speakerdir_for_speaker(speaker),
        '{}_{}{}.wav'.format(speaker, dataname, rep)
    )
    # Use wavio for broken .wav files
    w = wavio.read(fname)
    return (w.rate, w.data[:, 0])
#    return scipy.io.wavfile.read(fname)
    
def read_ecog_palate_trace(basepath, speaker, trange, dataname='Palate', element='PL', xdim=None, ydim=None, **kwargs):
    '''Read a palate data file and return a landmark dataframe of columns 'x' and 'y', plus 'landmark' column. kwargs (like rep) will be passed to read_ecog_speaker_data().'''
    paldf = read_ecog_speaker_data(
        basepath, speaker, dataname, **kwargs
    )
    tracetimes = (paldf.sec > trange[0]) & (paldf.sec < trange[1])
    palcols = ['{}_{}'.format(element, xdim), '{}_{}'.format(element, ydim)]
    landmarkdf = paldf.loc[tracetimes, palcols]
    landmarkdf.columns = ['x', 'y']
    landmarkdf = landmarkdf.assign(
        landmark=pd.Series(['palate'] * len(landmarkdf))
    )
    return landmarkdf

def read_ecog_speaker_data(basepath, speaker, dataname, rep=None, drop_prefixes=['EMPTY']):
    '''Read a UCSF EMA (ECOG) speaker data file into a DataFrame.
The directory name is formed from basepath and speaker.
The filename is formed from speaker, dataname, and the repetition (rep). The
rep parameter can be a string or an integer.
Empty columns (identified by empty or whitespace-only column names) are dropped.
'''
    snre = re.compile(r'\d+$')
    if rep is None or rep == '':
        rep = ''
    else:
        if not isinstance(rep, str):  # if rep is passed as an int
            rep = '_{:03d}'.format(rep)
        elif not rep.startswith('_'):
            rep = '_' + rep
    fname = os.path.join(
        basepath,
        ecog_speakerdir_for_speaker(speaker),
        '{}_{}{}.ndi'.format(speaker, dataname, rep)
    )
    
    df = pd.read_csv(fname, sep='\t')
    to_drop = [c for name in drop_prefixes for c in df.columns if c.startswith(name)]
    df = df.drop(to_drop, axis=1)

    if 'time' in df.columns:
        df = df.rename(columns={'time': 'sec'})

    # Calculate velocities for all coordinate columns and add as <coordinate>_vel columns.
    coordcols = [
        c for c in df.columns if c[-2:] in ['_x', '_y', '_z']
    ]
    df = df.join(df[coordcols].diff(), rsuffix='_vel')

#    return with_quats(df, sensors)
    return df

def read_marquette_speaker_data(basepath, speaker, dataname):
    '''Read Marquette EMA speaker data from a directory.'''
    spkpath = os.path.join(basepath, speaker)

    sensors = ["REF","TD","TL","TB","UL","LL","LC","MI","PL","OS","MS","UNK0","UNK1"]
    subcolumns = ["ID","Status","x","y","z","q0","qx","qy","qz"]
    better_head = \
        ['sec', 'measid', 'wavid'] + \
        ['{}_{}'.format(s, c) for s in sensors for c in subcolumns]
    coordcols = [
        '{}_{}'.format(s, d) for s in sensors for d in ['x', 'y', 'z']
    ]

    read_csv_kwargs = dict(
        sep='\t',
        header=None,            # The last three parameters
        skiprows=1,             # are used to override
        names=better_head       # the existing file header.
    )

    datadf = pd.read_csv(
        os.path.join(spkpath, 'Data', '{}_{}.tsv'.format(speaker, dataname)),
        **read_csv_kwargs
    )
    # Calculate velocities for all coordinate columns and add as <coordinate>_vel columns.
    datadf = datadf.join(datadf[coordcols].diff(), rsuffix='_vel')

    paldf = pd.read_csv(
        os.path.join(
            spkpath, 'Calibration', 'Palate',
            '{}_palatetrace.tsv'.format(speaker)
        ),
        **read_csv_kwargs
    )

    bpdf = pd.read_csv(
        os.path.join(
            spkpath, 'Calibration', 'Biteplate',
            '{}_Biteplate.tsv'.format(speaker)
        ),
        **read_csv_kwargs
    )

    rotdf = pd.read_csv(
        os.path.join(
            spkpath, 'Calibration', 'Biteplate',
            '{}_Biteplate_Rotation.txt'.format(speaker)
        ),
        sep='\t',
        header=None
    )
    
#    return (with_quats(datadf, sensors), with_quats(paldf, sensors),
#            with_quats(bpdf, sensors), rotdf)
    return (datadf, paldf, bpdf, rotdf)


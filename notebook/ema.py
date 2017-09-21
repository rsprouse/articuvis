import os, re
import pandas as pd
import scipy.io.wavfile
import wavio

def speaker_as_int_str(speaker):
    '''Take a speaker identifier and return the speaker as an str
representing an integer. Speaker identifiers may be strings like 'Subject_4',
'SN4, or '4' or integers.'''
    spkridre = re.compile(r'^(?:Subject_|SN)?(?P<subjnum>\d+)$')
    if isinstance(speaker, str):
        m = spkridre.search(speaker)
        if m is None:
            raise RuntimeError('Unrecognized speaker identifier.')
        int_str = m.group('subjnum')
    else:
        int_str = str(speaker)
    return int_str

class EmaEcogDataLoader():
    '''A class for loading EMA-ECOG data.'''
    def __init__(self, datadir, *args, **kwargs):
        super(EmaEcogDataLoader, self).__init__(*args, **kwargs)
        self.datadir = datadir
        self.speaker_map = self.get_speaker_map()

    def get_speaker_map(self):
        '''Find subject directories in datadir and return a dict that maps subject
numbers to utterances and repetitions.'''
        ddir = self.datadir
        spkrmap = {}
        snre = re.compile(r'Subject_(\d+)$')
        dirs = [
            os.path.join(ddir, o) for o in os.listdir(ddir) \
                if os.path.isdir(os.path.join(ddir, o))
        ]
        for d in dirs:
            m = snre.search(d)
            if m:
                spkrnum = m.group(1)
                tokenre = re.compile(r'^SN{}_(.+)_(\d+)\.ndi$'.format(spkrnum))
                utterances = {}
                for f in os.listdir(d):
                    tm = tokenre.search(f)
                    if tm and os.path.isfile(os.path.join(self.datadir, d, f)):
                        utt = tm.group(1)
                        rep = tm.group(2)
                        try:
                            utterances[utt].append(rep)
                        except KeyError:
                            utterances[utt] = [rep]
                spkrmap[spkrnum] = utterances
        return spkrmap

    def get_audio(self, speakerid, dataname, rep, channel):
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
        spkr_int_str = speaker_as_int_str(speakerid)
        fname = os.path.join(
            self.datadir,
            'Subject_{}'.format(spkr_int_str),
            'SN{}_{}{}.wav'.format(spkr_int_str, dataname, rep)
        )
        # Use wavio for broken .wav files
        w = wavio.read(fname)
        return (w.rate, w.data[:, channel])
#        return scipy.io.wavfile.read(fname)
    
    def get_palate_trace(self, speakerid, trange, dataname='Palate', element='PL', xdim=None, ydim=None, **kwargs):
        '''Read a palate data file and return a landmark dataframe of columns 'x' and 'y', plus 'landmark' column. kwargs (like rep) will be passed to get_speaker_utt().'''
        paldf = self.get_speaker_utt(
            speakerid, dataname, **kwargs
        )
        tracetimes = (paldf.sec > trange[0]) & (paldf.sec < trange[1])
        palcols = ['{}_{}'.format(element, xdim), '{}_{}'.format(element, ydim)]
        landmarkdf = paldf.loc[tracetimes, palcols]
        landmarkdf.columns = ['x', 'y']
        landmarkdf = landmarkdf.assign(
            landmark=['palate'] * len(landmarkdf)
        )
        return landmarkdf

    def get_speaker_utt(self, speakerid, dataname, rep=None, drop_prefixes=['EMPTY']):
        '''Read a UCSF EMA (ECOG) speaker utterance into a DataFrame.
The directory name is formed from datadir and speaker.
The filename is formed from speaker, dataname, and the repetition (rep). The
rep parameter can be a string or an integer.
'''
        if rep is None or rep == '':
            rep = ''
        else:
            if not isinstance(rep, str):  # if rep is passed as an int
                rep = '_{:03d}'.format(rep)
            elif not rep.startswith('_'):
                rep = '_' + rep
        spkr_int_str = speaker_as_int_str(speakerid)
        fname = os.path.join(
            self.datadir,
            'Subject_{}'.format(spkr_int_str),
            'SN{}_{}{}.ndi'.format(spkr_int_str, dataname, rep)
        )
    
        df = pd.read_csv(fname, sep='\t')
        to_drop = [c for name in drop_prefixes for c in df.columns if c.startswith(name)]
        df = df.drop(to_drop, axis=1)

        if 'time' in df.columns:
            df = df.rename(columns={'time': 'sec'})

        # Calculate velocities for all coordinate columns and add as
        # <coordinate>_vel columns.
        coordcols = [c for c in df.columns if c[-2:] in ['_x', '_y', '_z']]
# TODO: smooth data before diff()
# TODO: don't calculate *_vel columns in this function
        df = df.join(df[coordcols].diff(), rsuffix='_vel')
        return df

    def get_speaker_list(self, sorted=True):
        '''Return a list of speakers, sorted by speaker number.'''
        spkrs = list(self.speaker_map.keys())
        if sorted is True:
            spkrs.sort(key=lambda x: int(x))
        return spkrs

    def get_utterance_list_for_speaker(self, speakerid, sorted=True):
        '''Return a list of utterances for a speaker.'''
        spkr_int_str = speaker_as_int_str(speakerid)
        utts = list(self.speaker_map[spkr_int_str].keys())
        if sorted is True:
            utts.sort()
        return utts
        
    def get_rep_list_for_speaker_utterance(self, speakerid, utt, sorted=True):
        '''Return a list of for a speaker utterance.'''
        spkr_int_str = speaker_as_int_str(speakerid)
        rep = list(self.speaker_map[spkr_int_str][utt])
        if sorted is True:
            rep.sort(key=lambda x: int(x))
        return rep

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


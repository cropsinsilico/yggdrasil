import copy
import warnings
from yggdrasil.communication.DedicatedFileBase import DedicatedFileBase
try:
    from Bio import SeqIO, SeqFeature
    from Bio.SeqRecord import SeqRecord
    from Bio.Seq import Seq
except ImportError:
    SeqIO = None
    SeqFeature = None
    SeqRecord = None
    Seq = None
    warnings.warn("biopython not installed so yggdrasil will not be "
                  "able to read some sequence data types")
# try:
#     import pysam
# except ImportError:
#     pysam = None
#     warnings.warn("pysam is not installed so yggdrasil will not be "
#                   "able to read some sequence data types")


class SequenceFileBase(DedicatedFileBase):  # pragma: seq
    r"""Base class for nucleotide/protein sequence I/O."""
    
    _stores_fd = True
    _sequence_types = {}

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration."""
        DedicatedFileBase.before_registration(cls)
        cls._extensions = [cls._sequence_types[cls._filetype]]
        cls._schema_subtype_description = f'{cls._filetype} sequence I/O'


class BioPythonFileBase(SequenceFileBase):  # pragma: seq
    r"""Base class for nucleotide/protein sequence I/O using biopython."""

    _schema_properties = {
        'piecemeal': {
            'type': 'boolean', 'default': False,
            'description': ('If possible read the the file '
                            'incrementally in multiple '
                            'messages. This should be used for '
                            'large files that cannot be loaded '
                            'into memory.')},
        'record_ids': {
            'type': 'array',
            'description': ('IDs of records to read/write. Other records '
                            'will be ignored.')}
    }
    _stores_fd = True
    _sequence_types = {
        'fasta': '.fasta',
        'fastq': '.fastq',
    }
    _valid_fields = ['id', 'description', 'dbxrefs']
    _has_annotations = True
    _has_separate_name = True

    def __init__(self, *args, **kwargs):
        self._records_iterator = None
        return super(BioPythonFileBase, self).__init__(*args, **kwargs)

    @property
    def records_iterator(self):
        r"""iterator: SeqRecord iterator."""
        assert self.fd and self.direction == 'recv'
        if self._records_iterator is None:
            if self.record_ids:
                index = SeqIO.index(self.fd, self._filetype)
                self._records_iterator = map(
                    lambda x: index[x], self.record_ids)
            else:
                self._records_iterator = SeqIO.parse(self.fd,
                                                     self._filetype)
        return self._records_iterator

    def ref2dict(self, x):
        r"""Convert a Reference object to a dictionary."""
        out = {}
        for k in ['authors', 'title', 'journal', 'medline_id',
                  'pubmed_id', 'comment']:
            out[k] = getattr(x, k)
        out['location'] = [self.loc2dict(y) for y in x.location]
        return out

    def dict2ref(self, x):
        r"""Convert a dictionary to a Reference object."""
        x['location'] = [self.dict2loc(y) for y in x.get('location', [])]
        out = SeqFeature.Reference()
        for k, v in x.items():
            setattr(out, k, v)
        return out

    def loc2dict(self, x):
        r"""Convert a FeatureLocation object to a dictionary."""
        out = {}
        for k in ['start', 'end', 'strand', 'ref', 'ref_db']:
            out[k] = getattr(x, k)
        return out

    def dict2loc(self, x):
        r"""Convert a dictionary to a FeatureLocation."""
        return SeqFeature.FeatureLocation(**x)

    def feature2dict(self, x):
        r"""Convert a Feature to a dictionary."""
        out = {'location': self.loc2dict(x.location)}
        for k in ['type', 'location_operator', 'id', 'qualifiers']:
            out[k] = getattr(x, k)
        return out

    def dict2feature(self, x):
        r"""Convert a dictionary to a Feature."""
        if x.get('location', False):
            x['location'] = self.dict2loc(x['location'])
        return SeqFeature.SeqFeature(**x)

    def record2dict(self, x):
        r"""Convert a SeqRecord to a dictionary."""
        out = {'seq': str(x.seq)}
        for k in self._valid_fields:
            if getattr(x, k):
                out[k] = getattr(x, k)
        # if 'references' in out.get('annotations', {}):
        #     out['annotations']['references'] = [
        #         self.ref2dict(ref) for ref in
        #         out['annotations']['references']]
        # if 'features' in out:
        #     out['features'] = [self.feature2dict(y) for
        #                        y in out['features']]
        return out

    def dict2record(self, x):
        r"""Covert a dictionary to a SeqRecord."""
        x = copy.deepcopy(x)
        x['seq'] = Seq(x['seq'])
        # y = x.get('annotations', {})
        # if 'references' in y:
        #     y['references'] = [self.dict2ref(ref) for
        #                        ref in y['references']]
        # if 'features' in x:
        #     x['features'] = [self.dict2feature(y) for y in x['features']]
        out = SeqRecord(**x)
        return out
    
    def _file_open(self, address, mode):
        self._last_size = 0
        return super(DedicatedFileBase, self)._file_open(address, mode)

    def _file_close(self):
        self._records_iterator = None
        return super(DedicatedFileBase, self)._file_close()

    def _dedicated_send(self, msg):
        if isinstance(msg, list):
            msg = [self.dict2record(x) for x in msg]
        else:
            msg = [self.dict2record(msg)]
        SeqIO.write(msg, self.fd, self._filetype)

    def _dedicated_recv(self):
        if self.piecemeal:
            # record = next(self.records_iterator)
            # print(record)
            # out = self.record2dict(record)
            out = self.record2dict(next(self.records_iterator))
        else:
            # record = list(self.records_iterator)
            # print(record[0].annotations)
            # out = [self.record2dict(x) for x in record]
            out = [self.record2dict(x) for x in self.records_iterator]
        return out

    @classmethod
    def get_testing_options(cls):
        r"""Method to return a dictionary of testing options for this
        class.

        Returns:
            dict: Dictionary of variables to use for testing. Items:
                kwargs (dict): Keyword arguments for comms tested with
                    the provided content.
                send (list): List of objects to send to test file.
                recv (list): List of objects that will be received from a
                    test file that was sent the messages in 'send'.
                contents (bytes): Bytes contents of test file created by
                    sending the messages in 'send'.

        """
        data = {
            'seq': 'MKQHKAMIVALIVICITAVVAALVTRKDLCEVHIRTGQTEVAVF',
            'id': 'YP_025292.1',
            'description': 'YP_025292.1 toxic membrane protein, small',
        }
        # if 'name' in cls._valid_fields:
        #     data['name'] = 'HokC'
        # if 'annotations' in cls._valid_fields:
        #     data['annotations'] = {
        #         'source': 'Paphiopedilum barbatum',
        #         'references': [
        #             {'title': 'Fake article',
        #              'authors': 'Doe, Jane',
        #              'locations': [
        #                  {'start': 0,
        #                   'end': 5}
        #              ]}
        #         ]
        #     }
        # if 'features' in cls._valid_fields:
        #     data['features'] = [{
        #         'location': {'start': 20, 'end': 21},
        #         'type': 'Site'
        #     }]
        if 'letter_annotations' in cls._valid_fields:
            data['letter_annotations'] = {
                'phred_quality': list(range(len(data['seq'])))
            }
        data = [data]
        out = {'kwargs': {},
               'exact_contents': False,
               'msg': data,
               'dict': False,
               'objects': [data],
               'send': [data],
               'recv': [data],
               'recv_partial': [[data]],
               'contents': (b'')}
        return out


# class PySamFileBase(SequenceFileBase):  # pragma: seq
#     r"""Base class for nucleotide/protein sequence I/O using pysam."""

#     _sequence_types = {
#         'sam': '.sam',
#         'bam': '.bam',
#         'cram': '.cram',
#         'bcf': '.bcf',
#         'vcf': '.vcf',
#     }

#     @property
#     def open_mode(self):
#         r"""str: Mode that should be used to open the file."""
#         out = super(PySamFileBase, self).open_mode
#         if self._filetype in ['bam', 'bcf']:
#             out += 'b'
#         elif self._filetype == 'cram':
#             out += 'c'
#         return out
        
#     def _file_open(self, address, mode):
#         if self._filetype in ['bcf', 'vcf']:
#             # TODO: Need header for writing
#             return pysam.VariantFile(address, mode)
#         return pysam.AlignmentFile(address, mode)

#     def _file_close(self):
#         self._fd.close()
#         self._fd = None

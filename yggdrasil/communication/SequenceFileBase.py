import os
import shutil
import copy
import warnings
from yggdrasil.communication.DedicatedFileBase import DedicatedFileBase
from yggdrasil.components import create_component_class
try:
    from Bio import SeqIO, SeqFeature
    from Bio.SeqRecord import SeqRecord
    from Bio.Seq import Seq
except ImportError:  # pragma: debug
    SeqIO = None
    SeqFeature = None
    SeqRecord = None
    Seq = None
    warnings.warn("biopython not installed so yggdrasil will not be "
                  "able to read some sequence data types")
try:
    import pysam
except ImportError:  # pragma: debug
    pysam = None
    warnings.warn("pysam is not installed so yggdrasil will not be "
                  "able to read some sequence data types")


class SequenceFileBase(DedicatedFileBase):
    r"""Base class for nucleotide/protein sequence I/O."""
    
    _stores_fd = True
    _sequence_types = {}
    _test_parameters = None

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration."""
        DedicatedFileBase.before_registration(cls)
        cls._extensions = [cls._sequence_types[cls._filetype]]
        cls._schema_subtype_description = f'{cls._filetype} sequence I/O'


class BioPythonFileBase(SequenceFileBase):
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

    @classmethod
    def is_installed(cls, language=None):
        r"""Determine if the necessary libraries are installed for this
        communication class.

        Args:
            language (str, optional): Specific language that should be checked
                for compatibility. Defaults to None and all languages supported
                on the current platform will be checked. If set to 'any', the
                result will be True if this comm is installed for any of the
                supported languages.

        Returns:
            bool: Is the comm installed.

        """
        return (language == 'python') and (SeqIO is not None)

    @property
    def records_iterator(self):
        r"""iterator: SeqRecord iterator."""
        assert self.fd and self.direction == 'recv'
        if self._records_iterator is None:
            if self.record_ids:
                index = SeqIO.index(self.current_address, self._filetype)
                self._records_iterator = map(
                    lambda x: index[x], self.record_ids)
            else:
                self._records_iterator = SeqIO.parse(self.fd,
                                                     self._filetype)
        return self._records_iterator

    # def ref2dict(self, x):
    #     r"""Convert a Reference object to a dictionary."""
    #     out = {}
    #     for k in ['authors', 'title', 'journal', 'medline_id',
    #               'pubmed_id', 'comment']:
    #         out[k] = getattr(x, k)
    #     out['location'] = [self.loc2dict(y) for y in x.location]
    #     return out

    # def dict2ref(self, x):
    #     r"""Convert a dictionary to a Reference object."""
    #     x['location'] = [self.dict2loc(y) for y in x.get('location', [])]
    #     out = SeqFeature.Reference()
    #     for k, v in x.items():
    #         setattr(out, k, v)
    #     return out

    # def loc2dict(self, x):
    #     r"""Convert a FeatureLocation object to a dictionary."""
    #     out = {}
    #     for k in ['start', 'end', 'strand', 'ref', 'ref_db']:
    #         out[k] = getattr(x, k)
    #     return out

    # def dict2loc(self, x):
    #     r"""Convert a dictionary to a FeatureLocation."""
    #     return SeqFeature.FeatureLocation(**x)

    # def feature2dict(self, x):
    #     r"""Convert a Feature to a dictionary."""
    #     out = {'location': self.loc2dict(x.location)}
    #     for k in ['type', 'location_operator', 'id', 'qualifiers']:
    #         out[k] = getattr(x, k)
    #     return out

    # def dict2feature(self, x):
    #     r"""Convert a dictionary to a Feature."""
    #     if x.get('location', False):
    #         x['location'] = self.dict2loc(x['location'])
    #     return SeqFeature.SeqFeature(**x)

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
    def get_testing_options(cls, piecemeal=False, **kwargs):
        r"""Method to return a dictionary of testing options for this
        class.

        Args:
            piecemeal (bool, optional): If True, the test data will be
                piecemeal.

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
        if not piecemeal:
            data = [data]
        out = {'kwargs': {},
               'exact_contents': False,
               'msg': data,
               'dict': False,
               'objects': [data],
               'send': [data],
               'recv': [data],
               'recv_partial': [[data]]}
        if cls._test_parameters:
            out.update(cls._test_parameters)
        if piecemeal:
            out['recv_kwargs'] = {'piecemeal': True,
                                  'record_ids': ['YP_025292.1']}
        return out


class PySamFileBase(SequenceFileBase):
    r"""Base class for nucleotide/protein sequence I/O using pysam."""

    _schema_properties = {
        'header': {
            'type': 'object',
            'description': ('Header defining sequence identifiers. A '
                            'header is required for writing SAM, BAM, '
                            'and CRAM files.')
        },
        'flush_on_write': {
            'type': 'boolean', 'default': False,
            'description': ('If true, the file will be flushed when '
                            'written to.')
        },
        'regions': {
            'type': 'array', 'default': [],
            'items': {
                'type': 'object',
                'required': ['name'],
                'properties': {
                    'name': {'type': 'string'},
                    'start': {'type': 'integer'},
                    'end': {'type': 'integer'}
                }
            },
            'description': ('Region parameters (reference name, start, '
                            'and end) defining the regions that should '
                            'be read. If not provided, all regions will '
                            'be read.')
        },
        'index': {
            'type': 'string',
            'description': ('Path to file containing index if different '
                            'from the standard naming convention for '
                            'BAM and CRAM files.')
        }
    }
    _sequence_types = {
        'sam': '.sam',
        'bam': '.bam',
        'cram': '.cram',
        'bcf': '.bcf',
        'vcf': '.vcf',
    }
    _sam_header_fields = []
    _vcf_header_fields = [
        'version', 'contigs', 'filters', 'formats', 'info', 'samples']
    _sam_data_fields = [
        'query_name', 'query_sequence', 'flag', 'reference_id',
        'reference_start', 'mapping_quality', 'cigar',
        'next_reference_id', 'next_reference_start', 'template_length',
        'query_qualities', 'tags']
    _vcf_data_fields = [
        'contig', 'start', 'stop', 'alleles', 'id', 'qual', 'filter',
        'info', 'samples']
    _stores_fd = False
    _requires_refresh = True
    concats_as_str = True

    def _init_before_open(self, **kwargs):
        r"""Initialization steps that should be performed after base
        class, but before the comm is opened."""
        out = super(PySamFileBase, self)._init_before_open(**kwargs)
        if self.direction == 'recv' and not self.regions:
            self.regions = [{}]
        elif self.direction == 'send':
            self.regions = []
        self._remaining_regions = copy.deepcopy(self.regions)
        self._processed_regions = []
        self._processed_iters = 0
        self._region_iterator = None
        self._header_size = None
        self._temp_address = None
        self._next_region = None
        self._index_created = False
        if self.append:
            self.flush_on_write = True
        return out

    @classmethod
    def is_installed(cls, language=None):
        r"""Determine if the necessary libraries are installed for this
        communication class.

        Args:
            language (str, optional): Specific language that should be checked
                for compatibility. Defaults to None and all languages supported
                on the current platform will be checked. If set to 'any', the
                result will be True if this comm is installed for any of the
                supported languages.

        Returns:
            bool: Is the comm installed.

        """
        return (language == 'python') and (pysam is not None)
    
    @property
    def open_mode(self):
        r"""str: Mode that should be used to open the file."""
        out = super(PySamFileBase, self).open_mode
        out = out.replace('a', 'w')
        if self._filetype in ['bam', 'bcf']:
            out += 'b'
        elif self._filetype == 'cram':
            out += 'c'
        return out
        
    @property
    def current_region(self):
        r"""dict: Current region."""
        if self._region_iterator is None:
            param = self._remaining_regions[0]
            self._region_iterator = self._external_fd.fetch(
                param.get('name', None), param.get('start', None),
                param.get('end', None))
            self._processed_iters = 0
        out = self._next_region
        try:
            self._processed_iters += 1
            self._next_region = next(self._region_iterator)
        except StopIteration:
            self._processed_regions.append(self._remaining_regions[0])
            del self._remaining_regions[0]
            self._region_iterator = None
        if out is None:
            out = self.current_region
        return out

    def advance_in_series(self, series_index=None):
        r"""Advance to a certain file in a series.

        Args:
            series_index (int, optional): Index of file in the series that
                should be moved to. Defaults to None and call will advance to
                the next file in the series.

        Returns:
            bool: True if the file was advanced in the series, False otherwise.

        """
        if self.is_series:
            self._processed_regions = []
            self._processed_iters = 0
        advanced = super(PySamFileBase, self).advance_in_series(
            series_index=series_index)
        return advanced
    
    @property
    def _file_size_recv(self):
        r"""int: Current size of file."""
        return self.file_size - len(self._remaining_regions)

    def series_file_size(self, fname):
        r"""int: Size of file in series."""
        return (super(PySamFileBase, self).series_file_size(fname)
                - self.header_size)
        
    @classmethod
    def _file_class(cls):
        if cls._filetype in ['bcf', 'vcf']:
            return pysam.VariantFile
        else:
            return pysam.AlignmentFile

    def _flush_send(self):
        self._file_close(in_flush=True)
        self._file_open(self.current_address, self.open_mode,
                        in_flush=True)
        cls = self._file_class()
        try:
            with cls(self.current_address,
                     self.open_mode.replace('w', 'r')) as fd:
                for x in fd.fetch():
                    self._external_fd.write(x)
        except ValueError:
            pass

    @classmethod
    def _has_index(cls):
        return (cls._filetype in ['bam', 'cram'])

    @classmethod
    def _is_sam_based(cls):
        return (cls._filetype in ['sam', 'bam', 'cram'])

    @classmethod
    def index_filename(cls, address):
        r"""Get the name of the index file."""
        out = None
        if cls._filetype == 'bam':
            out = address + '.bai'
        elif cls._filetype == 'cram':
            out = address + '.crai'
        return out

    def create_index(self, address, overwrite=False):
        r"""Create an index file to accompany the file begin written/read
        if one is required."""
        index = self.index_filename(address)
        if index and os.path.isfile(address):
            index = address + '.bai'
            if ((overwrite or self._index_created
                 or not os.path.isfile(index))):
                pysam.index(address)
                self._index_created = True
                if os.path.isfile(index):
                    shutil.copystat(address, index)
                else:
                    return None
        return index

    @classmethod
    def remove_companion_files(cls, address):
        r"""Remove companion files that are created when writing to a
        file

        Args:
            address (str): Address for the filename.

        """
        if not cls._has_index():
            return
        index_address = cls.index_filename(address)
        if os.path.isfile(index_address):
            os.remove(index_address)
        
    def _dedicated_open(self, address, mode, in_flush=False):
        kws = {}
        fname = address
        cls = self._file_class()
        if self.direction == 'send':
            kws['header'] = self.dict2header(self.header)
            if self.flush_on_write:
                self._temp_address = os.path.join(
                    os.path.split(address)[0],
                    'tmp_' + os.path.split(address)[1])
                fname = self._temp_address
        elif self._has_index():
            index = self.index
            if not self.index:
                index = self.create_index(fname)
            kws['index_filename'] = index
        if self.direction == 'send' and self.append and not in_flush:
            self._flush_send()
            return
        self._external_fd = cls(fname, mode, **kws)
        if self.direction == 'recv':
            processed_iters = self._processed_iters
            allsheets = copy.deepcopy(self.regions)
            self._processed_iters = 0
            self._remaining_regions = [
                k for k in allsheets if k not in self._processed_regions]
            while self._processed_iters != processed_iters:
                self.current_region
            self._last_size = self.header_size
        else:
            if ((self._filetype in ['bam', 'cram', 'vcf', 'bcf']
                 and not in_flush)):
                self._flush_send()
            elif self.flush_on_write and not os.path.isfile(address):
                shutil.copy2(self._temp_address, address)
        return self._external_fd

    @property
    def header_size(self):
        if self._header_size is None:
            parts = os.path.split(self.current_address)
            fname = os.path.join(parts[0], 'head_' + parts[1])
            try:
                cls = self._file_class()
                kws = {}
                if self._is_sam_based():
                    kws['template'] = self._external_fd
                else:
                    kws['header'] = self._external_fd.header
                fd = cls(fname, self.open_mode.replace('r', 'w'), **kws)
                fd.close()
                self._header_size = os.stat(fname).st_size
            finally:
                if os.path.isfile(fname):
                    os.remove(fname)
        return self._header_size
    
    def _dedicated_close(self, in_flush=False):
        if self._external_fd:
            self._external_fd.close()
        self._external_fd = None
        self._region_iterator = None
        self._next_region = None
        if self.direction == 'send' and os.path.isfile(self._temp_address):
            shutil.copy2(self._temp_address, self.current_address)
            if self._has_index():
                self.create_index(self._temp_address, overwrite=True)
                shutil.copy2(self.index_filename(self._temp_address),
                             self.index_filename(self.current_address))
                os.remove(self.index_filename(self._temp_address))
            os.remove(self._temp_address)

    def _dedicated_send(self, msg):
        msg = self.dict2region(msg, header=self._external_fd.header)
        self._external_fd.write(msg)
        if self.flush_on_write:
            self._flush_send()

    def _dedicated_recv(self):
        msg = self.current_region
        return self.region2dict(msg)

    @classmethod
    def _data_fields(cls):
        if cls._is_sam_based():
            return cls._sam_data_fields
        else:
            return cls._vcf_data_fields

    @classmethod
    def _header_fields(cls):
        assert not cls._is_sam_based()
        return cls._vcf_header_fields

    @classmethod
    def region2dict(cls, x):
        out = {}
        for k in cls._data_fields():
            out[k] = getattr(x, k)
            if k in ['cigar', 'tags']:
                out[k] = [list(xx) for xx in out[k]]
            elif k in ['alleles']:
                out[k] = list(out[k])
            elif k in ['filter', 'info']:
                out[k] = [kk for kk in out[k].keys()]
            elif k in ['samples']:
                out[k] = [{kkk: list(vvv) for kkk, vvv in vv.items()}
                          for vv in out[k].values()]
            if not out[k] and isinstance(out[k], (list, dict, tuple)):
                del out[k]
        if 'query_qualities' in out:
            out['query_qualities'] = pysam.array_to_qualitystring(
                out['query_qualities'])
        return out

    @classmethod
    def dict2region(cls, x, header=None):
        if cls._is_sam_based():
            out = pysam.AlignedSegment()
            for k in cls._data_fields():
                if k in x:
                    if k == 'query_qualities':
                        setattr(out, k, pysam.qualitystring_to_array(x[k]))
                    elif k in ['cigar', 'tags']:
                        setattr(out, k, tuple(tuple(xx) for xx in x[k]))
                    else:
                        setattr(out, k, x[k])
        else:
            assert header is not None
            out = header.new_record(**copy.deepcopy(x))
        return out

    @classmethod
    def record2dict(cls, x):
        out = dict(x)
        out.pop('IDX', None)
        if 'Description' in out:
            out['Description'] = out['Description'].strip('"')
        for k in ['length', 'assembly']:
            out.pop(k, None)
        return out

    @classmethod
    def header2dict(cls, x):
        out = {}
        if isinstance(x, dict):
            return x
        for k in cls._header_fields():
            out[k] = getattr(x, k)
            if k in ['contigs']:
                out[k[:-1]] = {
                    kk: cls.record2dict(vv.header_record)
                    for kk, vv in out.pop(k).items()}
            elif k in ['filters', 'formats']:
                out[k[:-1].upper()] = {
                    kk: cls.record2dict(vv.record)
                    for kk, vv in out.pop(k).items()}
            elif k in ['info']:
                out[k.upper()] = {
                    kk: cls.record2dict(vv.record)
                    for kk, vv in out.pop(k).items()}
            elif k in ['samples']:
                out[k] = list(out[k])
        return out

    @classmethod
    def dict2header(cls, x):
        if cls._is_sam_based():
            return x
        out = pysam.VariantHeader()
        for k, v in x.items():
            if k in ['version']:
                continue
            elif k in ['samples']:
                out.add_samples(*x[k])
                continue
            elif k in ['contig', 'FILTER', 'FORMAT', 'INFO']:
                for kk, vv in v.items():
                    out.add_meta(key=k, items=vv.items())
        return out

    @classmethod
    def get_testing_options(cls, test_dir=None, **kwargs):
        r"""Method to return a dictionary of testing options for this
        class."""
        if cls._is_sam_based():
            a = pysam.AlignedSegment()
            a.query_name = "read_28833_29006_6945"
            a.query_sequence = "AGCTTAGCTAGCTACCTATATCTTGGTCTTGGCCG"
            a.flag = 99
            a.reference_id = 0
            a.reference_start = 0  # 32
            a.mapping_quality = 20
            a.cigar = ((0, 10), (2, 1), (0, 25))
            a.next_reference_id = -1
            a.next_reference_start = -1
            a.template_length = 167
            a.query_qualities = pysam.qualitystring_to_array(
                "<<<<<<<<<<<<<<<<<<<<<:<9/,&,22;;<<<")
            a.tags = (("NM", 1),
                      ("RG", "L1"))
            header = {'HD': {'VN': '1.0'},
                      'SQ': [{'LN': 1575, 'SN': 'chr1'},
                             {'LN': 1584, 'SN': 'chr2'}],
                      'RG': [{"ID": "L1",
                              }]}
        else:
            assert test_dir is not None
            fname = os.path.join(test_dir, 'data', 'example.vcf')
            with pysam.VariantFile(fname, 'r') as fd:
                a = next(fd.fetch())
                header = a.header
        header = cls.header2dict(header)
        data = cls.region2dict(a)
        out = {
            'kwargs': {'header': header, 'flush_on_write': True},
            'exact_contents': False,
            'msg': data,
            'dict': False,
            'objects': [data],
            'send': [data],
            'recv': [data],
            'recv_partial': [[data]],
            'contents': None,
        }
        out['driver_send_kwargs'] = {'header': header}
        return out


_biopython_classes = [
    ('FASTA', {
        '_filetype': 'fasta',
        '_test_parameters': {
            'contents': (
                b'>YP_025292.1 toxic membrane protein, small\nMKQHKAMI'
                b'VALIVICITAVVAALVTRKDLCEVHIRTGQTEVAVF\n'
            )
        },
    }),
    ('FASTQ', {
        '_filetype': 'fastq',
        '_valid_fields': BioPythonFileBase._valid_fields + [
            'letter_annotations'],
        '_test_parameters': {
            'contents': (
                b'@YP_025292.1 toxic membrane protein, small\nMKQHKAMI'
                b'VALIVICITAVVAALVTRKDLCEVHIRTGQTEVAVF\n+\n!"#$%&\'()*'
                b'+,-./0123456789:;<=>?@ABCDEFGHIJKL\n'
            )
        }
    }),
]
for name, attr in _biopython_classes:
    create_component_class(globals(), BioPythonFileBase,
                           f'{name}FileComm', attr)


for name in PySamFileBase._sequence_types.keys():
    create_component_class(globals(), PySamFileBase,
                           f'{name.upper()}FileComm', {'_filetype': name})

import struct
import hashlib
import bz2
import sys
import bsdiff4
import io
import os
try:
    import lzma
except ImportError:
    from backports import lzma

import update_metadata_pb2 as um


def extract_payload(payload_file_path, out='output', diff=False, old='old', images=''):
    def u32(x):
        return struct.unpack('>I', x)[0]

    def u64(x):
        return struct.unpack('>Q', x)[0]

    def verify_contiguous(exts):
        blocks = 0

        for ext in exts:
            if ext.start_block != blocks:
                return False

            blocks += ext.num_blocks

        return True

    def data_for_op(op, out_file, old_file):
        payload_file.seek(data_offset + op.data_offset)
        data = payload_file.read(op.data_length)

        # assert hashlib.sha256(data).digest() == op.data_sha256_hash, 'operation data hash mismatch'

        if op.type == op.REPLACE_XZ:
            dec = lzma.LZMADecompressor()
            data = dec.decompress(data)
            out_file.seek(op.dst_extents[0].start_block * block_size)
            out_file.write(data)
        elif op.type == op.REPLACE_BZ:
            dec = bz2.BZ2Decompressor()
            data = dec.decompress(data)
            out_file.seek(op.dst_extents[0].start_block * block_size)
            out_file.write(data)
        elif op.type == op.REPLACE:
            out_file.seek(op.dst_extents[0].start_block * block_size)
            out_file.write(data)
        elif op.type == op.SOURCE_COPY:
            if not diff:
                print("SOURCE_COPY supported only for differential OTA")
                sys.exit(-2)
            out_file.seek(op.dst_extents[0].start_block * block_size)
            for ext in op.src_extents:
                old_file.seek(ext.start_block * block_size)
                data = old_file.read(ext.num_blocks * block_size)
                out_file.write(data)
        elif op.type == op.SOURCE_BSDIFF:
            if not diff:
                print("SOURCE_BSDIFF supported only for differential OTA")
                sys.exit(-3)
            out_file.seek(op.dst_extents[0].start_block * block_size)
            tmp_buff = io.BytesIO()
            for ext in op.src_extents:
                old_file.seek(ext.start_block * block_size)
                old_data = old_file.read(ext.num_blocks * block_size)
                tmp_buff.write(old_data)
            tmp_buff.seek(0)
            old_data = tmp_buff.read()
            tmp_buff.seek(0)
            tmp_buff.write(bsdiff4.patch(old_data, data))
            n = 0
            tmp_buff.seek(0)
            for ext in op.dst_extents:
                tmp_buff.seek(n * block_size)
                n += ext.num_blocks
                data = tmp_buff.read(ext.num_blocks * block_size)
                out_file.seek(ext.start_block * block_size)
                out_file.write(data)
        elif op.type == op.ZERO:
            for ext in op.dst_extents:
                out_file.seek(ext.start_block * block_size)
                out_file.write(b'\x00' * ext.num_blocks * block_size)
        else:
            print("Unsupported type = %d" % op.type)
            sys.exit(-1)

        return data

    def dump_part(part):
        sys.stdout.write("Processing %s partition" % part.partition_name)
        sys.stdout.flush()

        with open('%s/%s.img' % (out, part.partition_name), 'wb') as out_file:
            h = hashlib.sha256()

            if diff:
                with open('%s/%s.img' % (old, part.partition_name), 'rb') as old_file:
                    for op in part.operations:
                        data = data_for_op(op, out_file, old_file)
                        sys.stdout.write(".")
                        sys.stdout.flush()
            else:
                for op in part.operations:
                    data = data_for_op(op, out_file, None)
                    sys.stdout.write(".")
                    sys.stdout.flush()

        print("Done")

    with open(payload_file_path, 'rb') as payload_file:
        magic = payload_file.read(4)
        assert magic == b'CrAU'

        file_format_version = u64(payload_file.read(8))
        assert file_format_version == 2

        manifest_size = u64(payload_file.read(8))

        metadata_signature_size = 0

        if file_format_version > 1:
            metadata_signature_size = u32(payload_file.read(4))

        manifest = payload_file.read(manifest_size)
        metadata_signature = payload_file.read(metadata_signature_size)

        data_offset = payload_file.tell()

        dam = um.DeltaArchiveManifest()
        dam.ParseFromString(manifest)
        block_size = dam.block_size

        if images == "":
            for part in dam.partitions:
                dump_part(part)
        else:
            images_list = images.split(",")
            for image in images_list:
                partition = [part for part in dam.partitions if part.partition_name == image]
                if partition:
                    dump_part(partition[0])
                else:
                    sys.stderr.write("Partition %s not found in payload!\n" % image)

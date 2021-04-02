import os


def model_function(in_buf):
    print("server%s(Python): %s" % (os.environ['YGG_MODEL_COPY'], in_buf))
    out_buf = in_buf
    return out_buf

import argparse
import os
import sys

import markovify


def load_training_data(filename):
    lines = []
    with open(filename, "r", encoding="utf8") as f:
        for line in f:
            if len(line) > 20:
                lines.append(line)
    return lines


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sentences", metavar="N", type=int, default=8,
                        help="how many sentences to output")
    parser.add_argument("--pdf", metavar="FILENAME", type=str,
                        help="output as a pdf file")
    parser.add_argument("--txt", metavar="FILENAME", type=str,
                        help="output as a plaintext file")
    args = parser.parse_args()

    data = load_training_data("data/mechanics-of-materials.txt")
    model = markovify.Text(" ".join(data))

    out_text = []
    for x in range(args.sentences):
        out_text.append(model.make_sentence(tries=100))
    out_text = " ".join(out_text)

    if args.pdf is None and args.txt is None:
        print(out_text)
        sys.exit(0)

    if args.pdf is not None:
        os.system("echo \"%s\" | enscript -p - | ps2pdf - %s" % (out_text.encode("utf8"), args.pdf))
    if args.txt is not None:
        with open(args.txt, "w", encoding="utf8") as f:
            f.write(out_text)
    sys.exit(0)
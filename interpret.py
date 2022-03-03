import re
import argparse
import sys
import xml.etree.ElementTree as ET


class Instruction:
    def __init__(self, order, opcode, arg1=None, arg2=None, arg3=None):
        self.order = order
        self.opcode = opcode
        self.arg1 = arg1
        self.arg2 = arg2
        self.arg3 = arg3


ap = argparse.ArgumentParser()
ap.add_argument("--source", nargs=1, help="help")
ap.add_argument("--input", nargs=1, help="help")

args = vars(ap.parse_args())

mode = ""
inputfile = ""
input_src = ""
src_src = ""
if args["source"] == None and args["input"] == None:
    ap.print_help()
    exit(1234)
if args["source"] != None and args["input"] != None:
    mode = "both"
    src_src = args["source"]
    input_src = args["input"]
elif args["source"]:
    mode = "source"
    input_src = sys.stdin.readlines()
    src_src = args["source"]
else:
    mode = "input"
    src_src = sys.stdin.readlines()
    input_src = args["input"]

xml_code = ' '.join(src_src)
tree = ET.parse(xml_code)
root = tree.getroot()

frames = [[]]
instructions = []
args = []
for elem in root.iter():
    if elem.tag == "instruction":
        for child in elem:
            args.append(child)
        inst = Instruction(elem.attrib['order'], elem.attrib['opcode'],
                           args[0] if args[0] else None, args[1] if len(
                               args) > 1 else None,
                           args[2] if len(args) > 2 else None)
        instructions.append(inst)

for inst in instructions:
    print(inst.opcode)
pass

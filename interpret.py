from posixpath import split
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


class Argument:
    def __init__(self, type, text, order):
        self.type = type
        self.text = text
        self.order = order


class Variable:
    def __init__(self, name, is_global, value, type):
        self.name = name
        self.is_global = is_global
        self.value = value
        self.type = type


def execute_inst(instruction):
    if(instruction.opcode == "DEFVAR"):
        defvar(instruction.arg1)
    if(instruction.opcode == "MOVE"):
        move(instruction.arg1, instruction.arg2)


def defvar(arg):
    split_arg = arg.text.split("@")
    is_global = False
    if split_arg[0] == "GF":
        is_global = True
    var = Variable(split_arg[1], is_global, None, None)
    global_vars[var.name] = var


def move(arg1, arg2):
    if arg1.type != "var":
        print("error type")
        exit(55)  # TODO

    split_arg1 = arg1.text.split("@")
    if split_arg1[0] == "GF":
        if split_arg1[1] not in global_vars:
            print("variable doesnt exist")
            exit(55)  # TODO
    # determine if symbol or literal
    global_vars[split_arg1[1]].value = arg2.text


def write(arg):
    # determine if symbol or literal
    print("TODO", end="")


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
            arg = Argument(child.attrib['type'], child.text, child.tag)
            args.append(arg)
            args.sort(key=lambda x: x.order)
        inst = Instruction(elem.attrib['order'], elem.attrib['opcode'],
                           args[0] if args[0] else None, args[1] if len(
                               args) > 1 else None,
                           args[2] if len(args) > 2 else None)
        instructions.append(inst)
    args = []

instructions.sort(key=lambda x: x.order)

# Start executing program
inst_pos = 0
frame_depth = 0
global_vars = {}
prg_len = len(instructions)
for inst_pos in range(prg_len):
    execute_inst(instructions[inst_pos])

print(global_vars["a"].value)
print(instructions[1].arg1.text)
pass

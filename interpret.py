from ast import Pass
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


class Counter:
    def __init__(self, file_line):
        self.file_line = file_line


class DataFrames:
    def __init__(self):
        self.frames = []
        self.temp_frame = None


global_vars = {}


def execute_inst(instruction, counter, input_src, data_frames):
    if(instruction.opcode == "DEFVAR"):
        defvar(instruction.arg1, data_frames)
    if(instruction.opcode == "MOVE"):
        move(instruction.arg1, instruction.arg2, data_frames)
    if(instruction.opcode == "WRITE"):
        write(instruction.arg1, data_frames)
    if(instruction.opcode == "READ"):
        read(instruction.arg1, instruction.arg2,
             counter, input_src, data_frames)
    if(instruction.opcode == "CREATEFRAME"):
        create_frame(data_frames)
    if(instruction.opcode == "PUSHFRAME"):
        push_frame(data_frames)
    if(instruction.opcode == "POPFRAME"):
        pop_frame(data_frames)


def create_frame(data_frames):
    data_frames.temp_frame = {}


def push_frame(data_frames):
    if data_frames.temp_frame == None:
        print("Temp frame doesnt exist")
        exit(55)
    data_frames.frames.push(data_frames.temp_frame)
    data_frames.temp_frame = None


def pop_frame(data_frames):
    if len(data_frames.frames) == 0:
        print("No frame to pop")
        exit(55)
    data_frames.temp_frame = data_frames.frames.pop()


def defvar(arg, data_frames):
    split_arg = arg.text.split("@")
    is_global = False
    if split_arg[0] == "GF":
        is_global = True
        var = Variable(split_arg[1], is_global, None, None)
        global_vars[var.name] = var
    elif split_arg[0] == "LF":
        var = Variable(split_arg[1], is_global, None, None)
        data_frames.frames[-1][var.name] = var
    elif split_arg[0] == "TF":
        var = Variable(split_arg[1], is_global, None, None)
        data_frames.temp_frame[var.name] = var


def move(arg1, arg2, data_frames):
    # check if var from arg1 exists
    split_arg1 = arg1.text.split("@")
    if split_arg1[0] == "GF":
        if split_arg1[1] not in global_vars:
            print("variable not in global_vars")
            exit(55)
    elif split_arg1[0] == "TF":
        pass  # TODO
    elif split_arg1[0] == "LF":
        pass  # TODO

    if arg2.type == "var":
        split_arg2 = arg2.text.split("@")
        if split_arg2[0] == "GF":
            if split_arg2[1] not in global_vars:
                print("variable not in global_vars")
                exit(55)
            global_vars[split_arg1[1]].value = global_vars[split_arg2[1]].value
        elif split_arg1[0] == "TF":
            pass  # TODO
        elif split_arg1[0] == "LF":
            pass  # TODO
    else:
        global_vars[split_arg1[1]].value = arg2.text


def write(arg, data_frames):
    if arg.type == "var":
        split_arg = arg.text.split("@")
        if split_arg[0] == "GF":
            if split_arg[1] not in global_vars:
                print("variable not in global_vars")
                exit(55)
            print(global_vars[split_arg[1]].value, end="")
        elif split_arg[0] == "TF":
            pass  # TODO
        elif split_arg[0] == "LF":
            pass  # TODO
    else:
        print(arg.text, end="")


def read(arg1, arg2, counter, input_src, data_frames):
    # check if var from arg1 exists
    split_arg1 = arg1.text.split("@")
    if split_arg1[0] == "GF":
        if split_arg1[1] not in global_vars:
            print("variable not in global_vars")
            exit(55)
    elif split_arg1[0] == "TF":
        pass  # TODO
    elif split_arg1[0] == "LF":
        pass  # TODO

    print("in read: " + input_src[counter.file_line])
    counter.file_line = counter.file_line+1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", nargs=1, help="help")
    ap.add_argument("--input", nargs=1, help="help")

    args = vars(ap.parse_args())

    input_mode = ""
    input_src = ""
    src_src = ""
    # One file must be present
    if args["source"] == None and args["input"] == None:
        ap.print_help()
        exit(1234)
    # both inputs given as files
    if args["source"] != None and args["input"] != None:
        input_mode = "file"
        src_src = args["source"]
        f = open(args["input"][0], "r")
        input_src = f.read()
        input_src = input_src.split('\n')
    # source code given as file
    elif args["source"]:
        input_src = sys.stdin
        src_src = args["source"]
    else:
        # input given as file
        input_mode = "file"
        src_src = sys.stdin
        f = open(args["input"], "r")
        input_src = f.read()
        input_src = input_src.split('\n')

    xml_code = open(src_src[0])
    tree = ET.parse(xml_code)
    root = tree.getroot()

    instructions = []
    args = [None, None, None]
    for elem in root.iter():
        if elem.tag == "instruction":
            for child in elem:
                arg = Argument(child.attrib['type'], child.text, child.tag)
                args.append(arg)
                if args[0] != None:
                    args.sort(key=lambda x: x.order)
                print(args)
            inst = Instruction(elem.attrib['order'], elem.attrib['opcode'],
                               args[0], args[1],)
            instructions.append(inst)
        args = [None, None, None]

    instructions.sort(key=lambda x: x.order)

    # Start executing program

    data_frames = DataFrames()
    counter = Counter(0)
    prg_len = len(instructions)
    for inst_pos in range(prg_len):
        execute_inst(instructions[inst_pos], counter, input_src, data_frames)

    # print(global_vars["a"].value)
    # print(instructions[1].arg1.text)
    pass


if __name__ == "__main__":
    main()

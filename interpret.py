from ast import Pass
from posixpath import split
import re
import argparse
import sys
import xml.etree.ElementTree as ET


class Instruction:
    def __init__(self, order, opcode, args):
        self.order = order
        self.opcode = opcode
        self.args = args


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
    def __init__(self, file_line, inst_counter):
        self.file_line = file_line
        self.inst_counter = inst_counter


class DataFrames:
    def __init__(self):
        self.frames = []
        self.temp_frame = None
        self.labels = {}


global_vars = {}


def execute_inst(instructions,prg_len, counter, input_src, data_frames):
    for counter.inst_counter in range(prg_len):
        if instructions[counter.inst_counter].opcode == "LABEL":
            label(instructions[counter.inst_counter], data_frames)
    counter.inst_counter = 0
    while counter.inst_counter < prg_len:
        if instructions[counter.inst_counter].opcode == "DEFVAR":
            defvar(instructions[counter.inst_counter].args, data_frames)
        if instructions[counter.inst_counter].opcode == "MOVE":
            move(instructions[counter.inst_counter].args, data_frames)
        if instructions[counter.inst_counter].opcode == "WRITE":
            write(instructions[counter.inst_counter].args, data_frames)
        if instructions[counter.inst_counter].opcode == "READ":
            read(instructions[counter.inst_counter].args, counter, input_src, data_frames)
        if instructions[counter.inst_counter].opcode == "CREATEFRAME":
            create_frame(data_frames)
        if instructions[counter.inst_counter].opcode == "PUSHFRAME":
            push_frame(data_frames)
        if instructions[counter.inst_counter].opcode == "POPFRAME":
            pop_frame(data_frames)
        if instructions[counter.inst_counter].opcode == "JUMP":
            jump(instructions[counter.inst_counter],instructions, data_frames, counter)
        counter.inst_counter += 1

def jump(instruction,instructions, data_frames, counter):
    if instruction.args[0].text not in data_frames.labels:
        print("Label doesnt exist")
        exit(52)
    help = data_frames.labels[instruction.args[0].text]
    jmp_index = instructions.index(help)
    counter.inst_counter = jmp_index
    #print("Jumping to inst number" + counter.inst_counter)


def label(instruction, data_frames):
    if instruction.args[0].text in data_frames.labels:
        print("Label aready defined")
        exit(52)
    data_frames.labels[instruction.args[0].text] = instruction

def create_frame(data_frames):
    data_frames.temp_frame = dict()


def push_frame(data_frames):
    if data_frames.temp_frame == None:
        print("Temp frame doesnt exist")
        exit(55)
    data_frames.frames.append(data_frames.temp_frame)
    data_frames.temp_frame = None


def pop_frame(data_frames):
    if len(data_frames.frames) == 0:
        print("No frame to pop")
        exit(55)
    data_frames.temp_frame = data_frames.frames.pop()


def defvar(args, data_frames):
    split_arg = args[0].text.split("@")
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


def move(args, data_frames):
    # check if var from arg1 exists

    split_arg1 = args[0].text.split("@")
    if split_arg1[0] == "GF":
        if split_arg1[1] not in global_vars:
            print("variable not in global_vars")
            exit(55)
    elif split_arg1[0] == "TF":
        if split_arg1[1] not in data_frames.temp_frame:
            print("variable not in temporary frame")
            exit(55)
    elif split_arg1[0] == "LF":
        if split_arg1[1] not in data_frames.frames[-1]:
            print("variable not in local frame")
            exit(55)

    if args[1].type == "var":
        split_arg2 = args[1].text.split("@")
        if split_arg2[0] == "GF":
            if split_arg2[1] not in global_vars:
                print("variable not in global_vars")
                exit(55)
            global_vars[split_arg1[1]].value = global_vars[split_arg2[1]].value
        elif split_arg1[0] == "TF":
            if split_arg2[1] not in data_frames.temp_frame:
                print("variable not in temporary frame")
                exit(55)
            data_frames.temp_frame[split_arg1[1]
                                   ].value = global_vars[split_arg2[1]].value
        elif split_arg1[0] == "LF":
            if split_arg2[1] not in data_frames.frames[-1]:
                print("variable not in local frame")
                exit(55)
            data_frames.frames[-1][split_arg1[1]
                                   ].value = global_vars[split_arg2[1]].value
    else:
        split_arg2 = args[1].text.split("@")
        if split_arg2[0] == "GF":
            global_vars[split_arg1[1]].value = args[1].text
        elif split_arg1[0] == "TF":
            data_frames.temp_frame[split_arg1[1]].value = args[1].text
        elif split_arg1[0] == "LF":
            data_frames.frames[-1][split_arg1[1]].value = args[1].text


def write(args, data_frames):
    if args[0].type == "var":
        split_arg = args[0].text.split("@")
        if split_arg[0] == "GF":
            if split_arg[1] not in global_vars:
                print("variable not in global_vars")
                exit(55)
            print(global_vars[split_arg[1]].value, end="")
        elif split_arg[0] == "TF":
            if split_arg[1] not in data_frames.temp_frame:
                print("variable not in temporary frame")
                exit(55)
            print(data_frames.temp_frame[split_arg[1]].value, end="")
        elif split_arg[0] == "LF":
            if split_arg[1] not in data_frames.frames[-1]:
                print("variable not in local frame")
                exit(55)
            print(data_frames.frames[-1][split_arg[1]].value, end="")
    else:
        print(args[0].text, end="")


def read(args, counter, input_src, data_frames):
    # check if var from arg1 exists
    split_arg1 = args[0].text.split("@")
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
    for elem in root.iter():
        if elem.tag == "instruction":
            for child in elem:
                arg = Argument(child.attrib['type'], child.text, child.tag)
                args.append(arg)
                if args[0] != None:
                    args.sort(key=lambda x: x.order)
            inst = Instruction(elem.attrib['order'], elem.attrib['opcode'],
                               args)
            instructions.append(inst)
        args = []

    instructions.sort(key=lambda x: int(x.order))

    # Start executing program

    data_frames = DataFrames()
    counter = Counter(0, 0)
    prg_len = len(instructions)

    execute_inst(instructions,prg_len, counter, input_src, data_frames)

    # print(global_vars["a"].value)
    # print(instructions[1].arg1.text)
    pass


if __name__ == "__main__":
    main()

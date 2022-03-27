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
        self.call_stack = []
        self.data_stack = []


global_vars = {}


def execute_inst(instructions,prg_len, counter, input_src, data_frames):
    for counter.inst_counter in range(prg_len):
        if instructions[counter.inst_counter].opcode == "LABEL":
            label(instructions[counter.inst_counter], data_frames)
    counter.inst_counter = 0
    while counter.inst_counter < prg_len:
        instruction = instructions[counter.inst_counter]
        if instruction.opcode == "DEFVAR":
            defvar(instruction.args, data_frames)
        if instruction.opcode == "MOVE":
            move(instruction.args, data_frames)
        if instruction.opcode == "WRITE":
            write(instruction.args, data_frames)
        if instruction.opcode == "READ":
            read(instruction.args, counter, input_src, data_frames)
        if instruction.opcode == "CREATEFRAME":
            create_frame(data_frames)
        if instruction.opcode == "PUSHFRAME":
            push_frame(data_frames)
        if instruction.opcode == "POPFRAME":
            pop_frame(data_frames)
        if instruction.opcode == "PUSHS":
            pushs(instruction.args, data_frames)
        if instruction.opcode == "JUMP":
            jump(instruction, instructions, data_frames, counter)
        if instruction.opcode == "CALL":
            data_frames.call_stack.append(counter.inst_counter+1)
            jump(instruction, instructions, data_frames, counter)
        if instruction.opcode == "RETURN":
            return_inst(data_frames, counter)
        if instruction.opcode in ["ADD", "MUL", "IDIV", "SUB"]:
            arithmetic(instruction.args, data_frames, instruction)
        if instruction.opcode in ["AND", "OR", "LT", "GT", "EQ"]:
            and_or(instruction.args, data_frames, instruction)
        if instruction.opcode == "NOT":
            not_inst(instruction.args, data_frames, instruction)
        if instruction.opcode == "PUSHS":
            pushs(instruction.args, data_frames)
        if instruction.opcode == "POPS":
            pops(instruction.args, data_frames)
        counter.inst_counter += 1

def return_inst(data_frames, counter):
    if not data_frames.call_stack:
        print("Call stack is empty")
        exit(56)
    jmp_index = data_frames.call_stack.pop()
    counter.inst_counter = jmp_index

def jump(instruction,instructions, data_frames, counter):
    if instruction.args[0].text not in data_frames.labels:
        print("Label doesnt exist")
        exit(52)
    inst = data_frames.labels[instruction.args[0].text]
    jmp_index = instructions.index(inst)
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


def pops(args, data_frames):
    #TODO pop types
    if args[0].type != "var":
        print("argument must be a var")
        exit(99)  #TODO
    check_var(args, data_frames)
    if not data_frames.data_stack:
        print("data stack empty")
        exit(56)
    stack_value = data_frames.data_stack.pop()

    split_arg1 = args[0].text.split("@")
    if split_arg1[0] == "GF":
        global_vars[split_arg1[1]].value = stack_value
    elif split_arg1[0] == "TF":
        data_frames.temp_frame[split_arg1[1]].value = stack_value
    elif split_arg1[0] == "LF":
        data_frames.frames[-1][split_arg1[1]].value = stack_value
    pass


def pushs(args, data_frames):
    if args[0].type == "var":
        split_arg = args[0].text.split("@")
        check_var_exists(split_arg[0], split_arg[1], data_frames)
        if split_arg[0] == "GF":
            data_frames.data_stack.append(global_vars[split_arg[1]].value)
        elif split_arg[0] == "TF":
            data_frames.data_stack.append(data_frames.temp_frame[split_arg[1]].value)
        elif split_arg[0] == "LF":
            data_frames.data_stack.append(data_frames.frames[-1][split_arg[1]].value)
    else:
        data_frames.data_stack.append(args[0].text)
    pass


def check_var_doesnt_exist(type, var_name, data_frames):
    if type == "GF":
        if var_name in global_vars:
            print("variable already defined")
            exit(55)
    elif type == "TF":
        if var_name in data_frames.temp_frame:
            print("variable already defined")
            exit(55)
    elif type == "LF":
        if var_name in data_frames.frames[-1]:
            print("variable already defined")
            exit(55)

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
        if data_frames.temp_frame is None:
            print("TF doesnt exist")
            exit(55)
        var = Variable(split_arg[1], is_global, None, None)
        data_frames.temp_frame[var.name] = var


def check_var_exists(type, var_name, data_frames):
    if type == "GF":
        if var_name not in global_vars:
            print("variable not in global_vars")
            exit(55)
    elif type == "TF":
        if data_frames.temp_frame is None:
            print("TF doesnt exist")
            exit(55)
        if var_name not in data_frames.temp_frame:
            print("variable not in temporary frame")
            exit(55)
    elif type == "LF":
        if var_name not in data_frames.frames[-1]:
            print("variable not in local frame")
            exit(55)


def check_var(args, data_frames):
    for arg in args:
        if arg.type == "var":
            split_arg = arg.text.split("@")
            check_var_exists(split_arg[0], split_arg[1], data_frames)


def move(args, data_frames):
    # check if var from arg1 exists
    #TODO move types
    check_var(args, data_frames)
    split_arg1 = args[0].text.split("@")
    if args[1].type == "var":
        split_arg2 = args[1].text.split("@")
        if split_arg2[0] == "GF":
            global_vars[split_arg1[1]].value = global_vars[split_arg2[1]].value
        elif split_arg1[0] == "TF":
            data_frames.temp_frame[split_arg1[1]].value = data_frames.temp_frame[split_arg2[1]].value
        elif split_arg1[0] == "LF":
            data_frames.frames[-1][split_arg1[1]].value = data_frames.frames[-1][split_arg2[1]].value
    else:
        if split_arg1[0] == "GF":
            global_vars[split_arg1[1]].value = args[1].text
        elif split_arg1[0] == "TF":
            data_frames.temp_frame[split_arg1[1]].value = args[1].text
        elif split_arg1[0] == "LF":
            data_frames.frames[-1][split_arg1[1]].value = args[1].text


def write(args, data_frames):
    if args[0].type == "var":
        split_arg = args[0].text.split("@")
        check_var_exists(split_arg[0], split_arg[1], data_frames)
        if split_arg[0] == "GF":
            print(global_vars[split_arg[1]].value, end="")
        elif split_arg[0] == "TF":
            print(data_frames.temp_frame[split_arg[1]].value, end="")
        elif split_arg[0] == "LF":
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


def get_var(argument, data_frames):
    split_arg2 = argument.text.split("@")
    if split_arg2[0] == "GF":
        value = global_vars[split_arg2[1]].value
    elif split_arg2[0] == "TF":
        value = data_frames.temp_frame[split_arg2[1]].value
    elif split_arg2[0] == "LF":
        value = data_frames.frames[-1][split_arg2[1]].value
    return value

def get_type(argument, data_frames):
    split_arg2 = argument.text.split("@")
    if split_arg2[0] == "GF":
        value = global_vars[split_arg2[1]].type
    elif split_arg2[0] == "TF":
        value = data_frames.temp_frame[split_arg2[1]].type
    elif split_arg2[0] == "LF":
        value = data_frames.frames[-1][split_arg2[1]].type
    return type


def check_int(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def check_bool(value):
    if value == "false" or value == "true":
        return True
    return False


def arithmetic(args, data_frames, instruction):
    if args[0].type != "var":
        print("first argument must be a var")
        exit(55)#TODO
    #TODO WRONG, NEED TO CHECK BETTER
    check_var(args, data_frames)
    split_arg1 = args[0].text.split("@")
    result = 0
    if args[1].type == "var":
        first_value = get_var(args[1], data_frames)
    else:
        first_value = args[1].text
    if args[2].type == "var":
        second_value = get_var(args[2], data_frames)
    else:
        second_value = args[2].text
    if not check_int(first_value) or not check_int(second_value):
        print("both arguments must be int")
        exit(32)#TODO
    first_value = int(first_value)
    second_value = int(second_value)
    if instruction.opcode == "ADD":
        result = first_value + second_value
    if instruction.opcode == "SUB":
        result = first_value - second_value
    if instruction.opcode == "MUL":
        result = first_value * second_value
    if instruction.opcode == "IDIV":
        if second_value == 0:
            print("Cannot divide by zero")
            exit(57)
        result = first_value // second_value
    if split_arg1[0] == "GF":
        global_vars[split_arg1[1]].value = result
    elif split_arg1[0] == "TF":
        data_frames.temp_frame[split_arg1[1]].value = result
    elif split_arg1[0] == "LF":
        data_frames.frames[-1][split_arg1[1]].value = result


def and_or(args, data_frames, instruction):
    if args[0].type != "var":
        print("first argument must be a var")
        exit(55)#TODO
    check_var(args, data_frames)
    split_arg1 = args[0].text.split("@")
    result = None
    if args[1].type == "var":
        first_value = get_var(args[1], data_frames)
        first_type = get_type(args[1], data_frames)
    else:
        first_value = args[1].text
    if args[2].type == "var":
        second_value = get_var(args[2], data_frames)
        second_type = get_type(args[1], data_frames)
    else:
        second_value = args[2].text

    if not check_bool(first_value) or not check_bool(second_value):
        print("both arguments must be bool")
        exit(32)  # TODO
    if instruction.opcode == "AND":
        result = first_value and second_value
    if instruction.opcode == "OR":
        result = first_value or second_value
    if instruction.opcode in ["LT", "GT", "EQ"]:
        logical(first_value, second_value, instruction)

    if split_arg1[0] == "GF":
        global_vars[split_arg1[1]].value = result
    elif split_arg1[0] == "TF":
        data_frames.temp_frame[split_arg1[1]].value = result
    elif split_arg1[0] == "LF":
        data_frames.frames[-1][split_arg1[1]].value = result

def logical(first_value, second_value, instruction):

    pass


def not_inst(args, data_frames, instruction):
    if args[0].type != "var":
        print("first argument must be a var")
        exit(55)#TODO
    check_var(args, data_frames)
    split_arg1 = args[0].text.split("@")
    result = None
    if args[1].type == "var":
        first_value = get_var(args[1], data_frames)
    else:
        first_value = args[1].text

    #TODO fix type check

    if not check_bool(first_value):
        print("argument must be bool")
        exit(32)  # TODO

    if first_value == "false":
        result = "true"
    if first_value == "true":
        result = "false"

    if split_arg1[0] == "GF":
        global_vars[split_arg1[1]].value = result
    elif split_arg1[0] == "TF":
        data_frames.temp_frame[split_arg1[1]].value = result
    elif split_arg1[0] == "LF":
        data_frames.frames[-1][split_arg1[1]].value = result

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

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
    def __init__(self, arg_type, value, order):
        self.arg_type = arg_type
        self.value = value
        self.order = order


class Variable:
    def __init__(self, name, is_global, value, arg_type, data_type):
        self.name = name
        self.is_global = is_global
        self.value = value
        self.arg_type = arg_type
        self.data_type = data_type


class Counter:
    def __init__(self, file_line, inst_counter):
        self.file_line = file_line
        self.inst_counter = inst_counter


class DataFrames:
    def __init__(self):
        self.global_vars = {}
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
        if instruction.opcode == "TYPE":
            type_inst(instruction.args, data_frames)
        if instruction.opcode == "INT2CHAR":
            type_inst(instruction.args, data_frames)
        if instruction.opcode == "STRI2INT":
            str2int(instruction.args, data_frames)
        if instruction.opcode == "CONCAT":
            concat(instruction.args, data_frames)
        if instruction.opcode == "GETCHAR":
            getchar(instruction.args, data_frames)
        if instruction.opcode == "SETCHAR":
            setchar(instruction.args, data_frames)
        if instruction.opcode == "STRLEN":
            strlen(instruction.args, data_frames)
        counter.inst_counter += 1


def str2int(args, data_frames):
    if args[0].arg_type != "var":
        print("first argument must be a var")
        exit(55)#TODO
    #TODO WRONG, NEED TO CHECK BETTER
    check_var(args, data_frames)
    split_arg0 = args[0].value.split("@")
    arg1 = get_var(args[1], data_frames)
    arg2 = get_var(args[2], data_frames)
    if arg1.data_type != "str" or arg2.data_type != "int":
        print("bad types")
        exit(55)#TODO
    arg2value = int(arg2.value)
    arg1value = arg1.value
    if arg2value > len(arg1value)-1 or arg2value < 0:
        print("Bad indeex in str2int")
        exit(58)
    result = ord(arg1value[arg2value])
    if split_arg0[0] == "GF":
        data_frames.global_vars[split_arg0[1]].value = result
    elif split_arg0[0] == "TF":
        data_frames.temp_frame[split_arg0[1]].value = result
    elif split_arg0[0] == "LF":
        data_frames.frames[-1][split_arg0[1]].value = result


def concat(args, data_frames):
    pass



def getchar(args, data_frames):
    pass


def setchar(args, data_frames):
    pass


def strlen(args, data_frames):
    pass


def return_inst(data_frames, counter):
    if not data_frames.call_stack:
        print("Call stack is empty")
        exit(56)
    jmp_index = data_frames.call_stack.pop()
    counter.inst_counter = jmp_index

def jump(instruction,instructions, data_frames, counter):
    if instruction.args[0].value not in data_frames.labels:
        print("Label doesnt exist")
        exit(52)
    inst = data_frames.labels[instruction.args[0].value]
    jmp_index = instructions.index(inst)
    counter.inst_counter = jmp_index
    #print("Jumping to inst number" + counter.inst_counter)


def label(instruction, data_frames):
    if instruction.args[0].value in data_frames.labels:
        print("Label aready defined")
        exit(52)
    data_frames.labels[instruction.args[0].value] = instruction

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
    if args[0].arg_type != "var":
        print("argument must be a var")
        exit(99)  #TODO
    check_var(args, data_frames)
    if not data_frames.data_stack:
        print("data stack empty")
        exit(56)
    stack_value = data_frames.data_stack.pop()

    split_arg1 = args[0].value.split("@")
    if split_arg1[0] == "GF":
        global_vars[split_arg1[1]].value = stack_value
    elif split_arg1[0] == "TF":
        data_frames.temp_frame[split_arg1[1]].value = stack_value
    elif split_arg1[0] == "LF":
        data_frames.frames[-1][split_arg1[1]].value = stack_value
    pass


def pushs(args, data_frames):
    if args[0].arg_type == "var":
        split_arg = args[0].value.split("@")
        check_var_exists(split_arg[0], split_arg[1], data_frames)
        if split_arg[0] == "GF":
            data_frames.data_stack.append(data_frames.global_vars[split_arg[1]])
        elif split_arg[0] == "TF":
            data_frames.data_stack.append(data_frames.temp_frame[split_arg[1]])
        elif split_arg[0] == "LF":
            data_frames.data_stack.append(data_frames.frames[-1][split_arg[1]])
    else:
        data_frames.data_stack.append(args[0])
    pass


def type_inst(args, data_frames):
        # check if var from arg1 exists
        # TODO move types
        check_var(args, data_frames)
        split_arg1 = args[0].value.split("@")
        if args[1].arg_type == "var":
            split_arg2 = args[1].value.split("@")
            if split_arg2[0] == "GF":
                global_vars[split_arg1[1]].value = global_vars[split_arg2[1]].arg_type
            elif split_arg1[0] == "TF":
                data_frames.temp_frame[split_arg1[1]].value = data_frames.temp_frame[split_arg2[1]].arg_type
            elif split_arg1[0] == "LF":
                data_frames.frames[-1][split_arg1[1]].value = data_frames.frames[-1][split_arg2[1]].arg_type
        else:
            if split_arg1[0] == "GF":
                global_vars[split_arg1[1]].value = args[1].arg_type
            elif split_arg1[0] == "TF":
                data_frames.temp_frame[split_arg1[1]].value = args[1].arg_type
            elif split_arg1[0] == "LF":
                data_frames.frames[-1][split_arg1[1]].value = args[1].arg_type


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
    split_arg = args[0].value.split("@")
    is_global = False
    if split_arg[0] == "GF":
        is_global = True
        var = Variable(split_arg[1], is_global, None, "", "")
        data_frames.global_vars[var.name] = var
    elif split_arg[0] == "LF":
        var = Variable(split_arg[1], is_global, None, "", "")
        data_frames.frames[-1][var.name] = var
    elif split_arg[0] == "TF":
        if data_frames.temp_frame is None:
            print("TF doesnt exist")
            exit(55)
        var = Variable(split_arg[1], is_global, None, "", "")
        data_frames.temp_frame[var.name] = var


def check_var_exists(type, var_name, data_frames):
    if type == "GF":
        if var_name not in data_frames.global_vars:
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
        if arg.arg_type == "var":
            split_arg = arg.value.split("@")
            check_var_exists(split_arg[0], split_arg[1], data_frames)


def move(args, data_frames):
    # check if var from arg1 exists
    #TODO move types
    check_var(args, data_frames)
    split_arg1 = args[0].value.split("@")
    if args[1].arg_type == "var":
        split_arg2 = args[1].value.split("@")
        if split_arg2[0] == "GF":
            data_frames.global_vars[split_arg1[1]] = data_frames.global_vars[split_arg2[1]]
        elif split_arg1[0] == "TF":
            data_frames.temp_frame[split_arg1[1]] = data_frames.temp_frame[split_arg2[1]]
        elif split_arg1[0] == "LF":
            data_frames.frames[-1][split_arg1[1]] = data_frames.frames[-1][split_arg2[1]]
    else:
        if split_arg1[0] == "GF":
            data_frames.global_vars[split_arg1[1]].value = args[1].value
            data_frames.global_vars[split_arg1[1]].arg_type = args[1].arg_type
            data_frames.global_vars[split_arg1[1]].data_type = args[1].arg_type
        elif split_arg1[0] == "TF":
            data_frames.temp_frame[split_arg1[1]].value = args[1].value
            data_frames.temp_frame[split_arg1[1]].arg_value = args[1].arg_type
            data_frames.temp_frame[split_arg1[1]].data_type = args[1].arg_type
        elif split_arg1[0] == "LF":
            data_frames.frames[-1][split_arg1[1]].value = args[1].value
            data_frames.frames[-1][split_arg1[1]].arg_type = args[1].arg_type
            data_frames.frames[-1][split_arg1[1]].data_type = args[1].arg_type


def write(args, data_frames):
    if args[0].arg_type == "var":
        split_arg = args[0].value.split("@")
        check_var_exists(split_arg[0], split_arg[1], data_frames)
        if split_arg[0] == "GF":
            res = data_frames.global_vars[split_arg[1]].value
        elif split_arg[0] == "TF":
            res = data_frames.temp_frame[split_arg[1]].value
        elif split_arg[0] == "LF":
            res = data_frames.frames[-1][split_arg[1]].value
    else:
        res = args[0].value
    if isinstance(res, str):
        res = res.replace('\\032', ' ')
    print(res, end="")


def read(args, counter, input_src, data_frames):
    check_var(args, data_frames)
    split_arg1 = args[0].value.split("@")
    if split_arg1[0] == "GF":
        data_frames.global_vars[split_arg1[1]].value = input_src[counter.file_line]
        #global_vars[split_arg1[1]].arg_type = get_type(args[1].arg_type)
    elif split_arg1[0] == "TF":
        data_frames.temp_frame[split_arg1[1]].value = input_src[counter.file_line]
        #data_frames.temp_frame[split_arg1[1]].arg_value = get_type(args[1].arg_type)
    elif split_arg1[0] == "LF":
        data_frames.frames[-1][split_arg1[1]].value = input_src[counter.file_line]
        #data_frames.frames[-1][split_arg1[1]].arg_type = get_type(args[1].arg_type)
    counter.file_line += 1


def get_var(argument, data_frames):
    split_arg2 = argument.value.split("@")
    if split_arg2[0] == "GF":
        value = data_frames.global_vars[split_arg2[1]]
    elif split_arg2[0] == "TF":
        value = data_frames.temp_frame[split_arg2[1]]
    elif split_arg2[0] == "LF":
        value = data_frames.frames[-1][split_arg2[1]]
    return value

def get_type(value):
    if value == "false" or "true":
        return "bool"
    if check_int(value):
        return "int"
    else:
        return "string"


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
    if args[0].arg_type != "var":
        print("first argument must be a var")
        exit(55)#TODO
    #TODO WRONG, NEED TO CHECK BETTER
    check_var(args, data_frames)
    split_arg1 = args[0].value.split("@")
    result = 0
    if args[1].arg_type == "var":
        first_value = get_var(args[1], data_frames)
    else:
        first_value = args[1].value
    if args[2].arg_type == "var":
        second_value = get_var(args[2], data_frames)
    else:
        second_value = args[2].value
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
        data_frames.global_vars[split_arg1[1]].value = result
    elif split_arg1[0] == "TF":
        data_frames.temp_frame[split_arg1[1]].value = result
    elif split_arg1[0] == "LF":
        data_frames.frames[-1][split_arg1[1]].value = result


def and_or(args, data_frames, instruction):
    if args[0].arg_type != "var":
        print("first argument must be a var")
        exit(55)#TODO
    check_var(args, data_frames)
    split_arg1 = args[0].value.split("@")
    result = None
    if args[1].arg_type == "var":
        first_value = get_var(args[1], data_frames)
        #first_type = get_type(args[1], data_frames)
    else:
        first_value = args[1]
    if args[2].arg_type == "var":
        second_value = get_var(args[2], data_frames)
        #second_type = get_type(args[1], data_frames)TODO
    else:
        second_value = args[2]
    if instruction.opcode in ["AND", "OR"]:
        if not check_bool(first_value) or not check_bool(second_value):
            print("both arguments must be bool")
            exit(32)  # TODO
    if instruction.opcode == "AND":
        result = first_value.value and second_value.value
    if instruction.opcode == "OR":
        result = first_value.value or second_value.value
    if instruction.opcode in ["LT", "GT", "EQ"]:
        result = logical(first_value, second_value, instruction)

    if split_arg1[0] == "GF":
        data_frames.global_vars[split_arg1[1]].value = result
        data_frames.global_vars[split_arg1[1]].arg_type = "bool"
    elif split_arg1[0] == "TF":
        data_frames.temp_frame[split_arg1[1]].value = result
        data_frames.temp_frame[split_arg1[1]].arg_type = "bool"
    elif split_arg1[0] == "LF":
        data_frames.frames[-1][split_arg1[1]].value = result
        data_frames.temp_frame[split_arg1[1]].arg_type = "bool"


def logical(first_value, second_value, instruction):
    if first_value.arg_type != second_value.arg_type:
        print("types not comparable")
        exit(55)#TODO
    if instruction.opcode == "LT":
        if first_value.arg_type == "int":
            result = int(first_value.value) < int(second_value.value)
        else:
            result = first_value.value < second_value.value
    if instruction.opcode == "GT":
        if first_value.arg_type == "int":
            result = int(first_value.value) > int(second_value.value)
        else:
            result = first_value.value > second_value.value
    if instruction.opcode == "EQ":
        if first_value.arg_type == "int":
            result = int(first_value.value) == int(second_value.value)
        else:
            result = first_value.value == second_value.value

    result = convert_bool_str(result)
    return result


def convert_bool_str(boolean):
    if boolean:
        return "true"
    return "false"


def not_inst(args, data_frames, instruction):
    if args[0].arg_type != "var":
        print("first argument must be a var")
        exit(55)#TODO
    check_var(args, data_frames)
    split_arg1 = args[0].value.split("@")
    result = None
    if args[1].arg_type == "var":
        first_value = get_var(args[1], data_frames)
    else:
        first_value = args[1].value

    #TODO fix type check

    if not check_bool(first_value):
        print("argument must be bool")
        exit(32)  # TODO

    if first_value == "false":
        result = "true"
    if first_value == "true":
        result = "false"

    if split_arg1[0] == "GF":
        data_frames.global_vars[split_arg1[1]].value = result
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
        src="file"
        src_src = args["source"]
        f = open(args["input"][0], "r")
        input_src = f.read()
        input_src = input_src.split('\n')
    # source code given as file
    elif args["source"]:
        src="file"
        input_src = sys.stdin
        input_src = input_src.read()
        input_src = input_src.split('\n')
        src_src = args["source"]
    else:
        # input given as file
        src="stdin"
        src_src = sys.stdin
        src_src = src_src.read()
        f = open(args["input"][0], "r")
        input_src = f.read()
        input_src = input_src.split('\n')

    if src != "stdin":
        xml_code = open(src_src[0])
        tree = ET.parse(xml_code)
        root = tree.getroot()
    else:
        root = ET.fromstring(src_src)

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
    # print(instructions[1].arg1.value)
    pass


if __name__ == "__main__":
    main()

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
    def __init__(self, name, is_global, value, arg_type):
        self.name = name
        self.is_global = is_global
        self.value = value
        self.arg_type = arg_type


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
        elif instruction.opcode == "MOVE":
            move(instruction.args, data_frames)
        elif instruction.opcode == "WRITE":
            write(instruction.args, data_frames)
        elif instruction.opcode == "READ":
            read(instruction.args, counter, input_src, data_frames)
        elif instruction.opcode == "CREATEFRAME":
            create_frame(data_frames)
        elif instruction.opcode == "PUSHFRAME":
            push_frame(data_frames)
        elif instruction.opcode == "POPFRAME":
            pop_frame(data_frames)
        elif instruction.opcode == "PUSHS":
            pushs(instruction.args, data_frames)
        elif instruction.opcode == "JUMP":
            jump(instruction, instructions, data_frames, counter)
        elif instruction.opcode in ["JUMPIFEQ", "JUMPIFNEQ"]:
            jump_eq(instruction, instructions, data_frames, counter)
        elif instruction.opcode == "CALL":
            data_frames.call_stack.append(counter.inst_counter+1)
            jump(instruction, instructions, data_frames, counter)
        elif instruction.opcode == "RETURN":
            return_inst(data_frames, counter)
        elif instruction.opcode in ["ADD", "MUL", "IDIV", "SUB"]:
            arithmetic(instruction.args, data_frames, instruction)
        elif instruction.opcode in ["AND", "OR", "LT", "GT", "EQ"]:
            and_or(instruction.args, data_frames, instruction)
        elif instruction.opcode == "NOT":
            not_inst(instruction.args, data_frames)
        elif instruction.opcode == "PUSHS":
            pushs(instruction.args, data_frames)
        elif instruction.opcode == "POPS":
            pops(instruction.args, data_frames)
        elif instruction.opcode == "TYPE":
            type_inst(instruction.args, data_frames)
        elif instruction.opcode == "INT2CHAR":
            int2char(instruction.args, data_frames)
        elif instruction.opcode in ["STRI2INT", "GETCHAR"]:
            str2int_getchar(instruction.args, data_frames, instruction)
        elif instruction.opcode == "CONCAT":
            concat(instruction.args, data_frames)
        elif instruction.opcode == "STRLEN":
            strlen(instruction.args, data_frames)
        elif instruction.opcode == "SETCHAR":
            setchar(instruction.args, data_frames)
        counter.inst_counter += 1

def unpack_args(args, data_frames):
    check_var(args, data_frames)
    operands = []
    for arg in args:
        if arg.arg_type == "var":
            operands.append(get_var(arg, data_frames))
        else:
            operands.append(arg)
    return operands


def str2int_getchar(args, data_frames, instruction):
    if args[0].arg_type != "var":
        print("first argument must be a var")
        exit(55)#TODO
    assigned_var = get_var(args[0], data_frames)
    operands = unpack_args(args, data_frames)
    if operands[1].arg_type != "str" or operands[2].arg_type != "int":
        print("bad types")
        exit(55)#TODO
    arg2value = int(operands[2].value)
    arg1value = operands[1].value
    if arg2value > len(arg1value)-1 or arg2value < 0:
        print("Bad indeex in str2int")
        exit(58)
    if instruction.opcode == "STRI2INT":
        result = ord(arg1value[arg2value])
        assigned_var.arg_type = "int"
    else:
        result = arg1value[arg2value]
        assigned_var.arg_type = "str"
    assigned_var.value = result


def concat(args, data_frames):
    if args[0].arg_type != "var":
        print("first argument must be a var")
        exit(55)#TODO
    assigned_var = get_var(args[0], data_frames)
    operands = unpack_args(args, data_frames)
    if operands[1].arg_type != "str" or operands[2].arg_type != "int":
        print("bad types")
        exit(55)#TODO
    assigned_var.value = operands[1].value + operands[2].value
    assigned_var.arg_type = "str"



def getchar(args, data_frames):
    if args[0].arg_type != "var":
        print("first argument must be a var")
        exit(55)  # TODO
    assigned_var = get_var(args[0], data_frames)
    operands = unpack_args(args, data_frames)
    if operands[1].arg_type != "str" or operands[2].arg_type != "int":
        print("bad types")
        exit(55)  # TODO
    arg2value = int(operands[2].value)
    arg1value = operands[1].value
    if arg2value > len(arg1value) - 1 or arg2value < 0:
        print("Bad indeex in str2int")
        exit(58)
    result = arg1value[arg2value]
    assigned_var.value = result
    assigned_var.arg_type = "str"


def setchar(args, data_frames):
    if args[0].arg_type != "var":
        print("first argument must be a var")
        exit(55)#TODO
    assigned_var = get_var(args[0], data_frames)
    operands = unpack_args(args, data_frames)
    if operands[1].arg_type != "int" or operands[2].arg_type != "str":
        print("bad types")
        exit(55)#TODO
    if operands[1].value < 0 or operands[1].value > len(operands[0].value):
        print("Bad index in setchar")
        exit(58)
    if operands[2].value == "":
        print("Empty string given in setchar")
        exit(58)
    operands[0].value[operands[1]] = operands[2].value[0]


def strlen(args, data_frames):
    if args[0].arg_type != "var":
        print("first argument must be a var")
        exit(55)  # TODO
    assigned_var = get_var(args[0], data_frames)
    operands = unpack_args(args, data_frames)
    first_operand = operands[1]
    # TODO maybe check for type
    if first_operand.arg_type != "str":
        print("Incompatible type")
        exit(999)#TODO
    result = len(first_operand.value)
    assigned_var.value = result
    assigned_var.arg_type = "int"


def int2char(args, data_frames):
    if args[0].arg_type != "var":
        print("first argument must be a var")
        exit(55)#TODO
    assigned_var = get_var(args[0], data_frames)
    operands = unpack_args(args, data_frames)
    first_operand = operands[1]
    #TODO maybe check for type
    try:
        result = chr(int(first_operand.value))
    except ValueError:
        print("Value for int2char out of range")
        exit(58)
    assigned_var.value = result
    assigned_var.arg_type = "str"


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

def jump_eq(instruction,instructions, data_frames, counter):
    if instruction.args[0].value not in data_frames.labels:
        print("Label doesnt exist")
        exit(52)
    operands = unpack_args(instruction.args, data_frames)
    if (operands[1].arg_type != operands[2].arg_type and
        operands[1].arg_type != "nil" and operands[2].arg_type != "nil"):
        print("incompatible operands")
        exit(53)
    if operands[1].arg_type == "int":
        operands[1].value = int(operands[1].value)
    if operands[2].arg_type == "int":
        operands[2].value = int(operands[2].value)
    if instruction.opcode == "JUMPIFEQ":
        if operands[1].value == operands[2].value:
            inst = data_frames.labels[instruction.args[0].value]
            jmp_index = instructions.index(inst)
            counter.inst_counter = jmp_index
    elif instruction.opcode == "JUMPIFNEQ":
        if operands[1].value != operands[2].value:
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
    if args[0].arg_type != "var":
        print("argument must be a var")
        exit(99)  #TODO
    check_var(args, data_frames)
    if not data_frames.data_stack:
        print("data stack empty")
        exit(56)
    stack_value = data_frames.data_stack.pop()
    assigned_var = get_var(args[0], data_frames)
    assigned_var.value = stack_value.value
    assigned_var.arg_type = stack_value.arg_type


def pushs(args, data_frames):
    if args[0].arg_type == "var":
        check_var(args, data_frames)
        assigning_var = get_var(args[0], data_frames)
        data_frames.data_stack.append(assigning_var)
    else:
        data_frames.data_stack.append(args[0])


def type_inst(args, data_frames):
    check_var(args, data_frames)
    assigned_var = get_var(args[0], data_frames)
    if args[1].arg_type == "var":
        assigning_var = get_var(args[1], data_frames)
        assigned_var.value = assigning_var.arg_type
        assigned_var.arg_type = "str"
    else:
        assigned_var.value = args[1].arg_type
        assigned_var.arg_type = "str"


def check_var_doesnt_exist(type_arg, var_name, data_frames):
    if type_arg == "GF":
        if var_name in global_vars:
            print("variable already defined")
            exit(55)
    elif type_arg == "TF":
        if var_name in data_frames.temp_frame:
            print("variable already defined")
            exit(55)
    elif type_arg == "LF":
        if var_name in data_frames.frames[-1]:
            print("variable already defined")
            exit(55)

def defvar(args, data_frames):
    split_arg = args[0].value.split("@")
    is_global = False
    if split_arg[0] == "GF":
        is_global = True
        var = Variable(split_arg[1], is_global, None, "")
        data_frames.global_vars[var.name] = var
    elif split_arg[0] == "LF":
        #TODO CHECK LF DOESNT EXIST
        var = Variable(split_arg[1], is_global, None, "")
        data_frames.frames[-1][var.name] = var
    elif split_arg[0] == "TF":
        if data_frames.temp_frame is None:
            print("TF doesnt exist")
            exit(55)
        var = Variable(split_arg[1], is_global, None, "")
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
        #TODO CHECK FRAME EXISTS
        if var_name not in data_frames.frames[-1]:
            print("variable not in local frame")
            exit(55)


def check_var(args, data_frames):
    for arg in args:
        if arg.arg_type == "var":
            split_arg = arg.value.split("@")
            check_var_exists(split_arg[0], split_arg[1], data_frames)


def move(args, data_frames):
    check_var(args, data_frames)
    assigned_var = get_var(args[0], data_frames)
    if args[1].arg_type == "var":
        assigned_var = get_var(args[1], data_frames)
    else:
        assigned_var.value = args[1].value
        assigned_var.arg_type = args[1].arg_type


def write(args, data_frames):
    if args[0].arg_type == "var":
        split_arg = args[0].value.split("@")
        check_var_exists(split_arg[0], split_arg[1], data_frames)
        res = get_var(args[0], data_frames)
    else:
        res = args[0]
    res = res.value
    if isinstance(res, str):
        res = re.sub(r'\\(\d{3})', lambda y: chr(int(y[1])), res)
        #res = res.replace('\\032', ' ')
    print(res, end="")


def read(args, counter, input_src, data_frames):
    check_var(args, data_frames)
    split_arg1 = args[0].value.split("@")
    assigned_var = get_var(args[0], data_frames)
    #assigned_var.value = input_src[counter.file_line]
    if args[1].value == "int":
        try:
            assigned_var.value = int(input_src[counter.file_line])
            assigned_var.arg_type = "int"
        except ValueError:
            assigned_var.value = "nil"
            assigned_var.arg_type = "nil"
            return
    elif args[1].value == "string":
        assigned_var.value = str(input_src[counter.file_line])
        assigned_var.arg_type = "str"
    elif args[1].value == "bool":
        assigned_var.arg_type = "bool"
        if input_src[counter.file_line] == "true":
            assigned_var.value = "true"
        else:
            assigned_var.value = "false"
    else:
        assigned_var.value = "nil"
        assigned_var.arg_type = "nil"

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
    result = 0
    operands = unpack_args(args, data_frames)
    first_operand = operands[1]
    second_operand = operands[2]
    if first_operand.arg_type != "int" or second_operand.arg_type != "int":
        print("both arguments must be int")
        exit(32)#TODO
    first_value = int(first_operand.value)
    second_value = int(second_operand.value)
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
    result_var = get_var(args[0], data_frames)
    result_var.value = result
    result_var.arg_type = "int"


def and_or(args, data_frames, instruction):
    if args[0].arg_type != "var":
        print("first argument must be a var")
        exit(55)#TODO
    result = None
    operands = unpack_args(args, data_frames)
    first_operand = operands[1]
    second_operand = operands[2]
    if instruction.opcode in ["AND", "OR"]:
        if first_operand.arg_type != "bool" or second_operand.arg_type != "bool":
            print("both arguments must be bool")
            exit(32)  # TODO
    first_value = convert_str_bool(first_operand.value)
    second_value = convert_str_bool(second_operand.value)
    if instruction.opcode == "AND":
        result = first_value and second_value
    if instruction.opcode == "OR":
        result = first_value or second_value
    if instruction.opcode in ["LT", "GT", "EQ"]:
        result = logical(first_operand, second_operand, instruction)

    result_var = get_var(args[0], data_frames)
    result_var.value = convert_bool_str(result)
    result_var.arg_type = "bool"


def logical(first_operand, second_operand, instruction):
    if first_operand.arg_type != second_operand.arg_type:
        print("types not comparable")
        exit(55)#TODO
    if instruction.opcode == "LT":
        if first_operand.arg_type == "int":
            result = int(first_operand.value) < int(second_operand.value)
        else:
            result = first_operand.value < second_operand.value
    if instruction.opcode == "GT":
        if first_operand.arg_type == "int":
            result = int(first_operand.value) > int(second_operand.value)
        else:
            result = first_operand.value > second_operand.value
    if instruction.opcode == "EQ":
        if first_operand.arg_type == "int":
            #TODO maybe useless
            result = int(first_operand.value) == int(second_operand.value)
        else:
            result = first_operand.value == second_operand.value

    return convert_bool_str(result)


def convert_bool_str(boolean):
    if boolean:
        return "true"
    return "false"


def convert_str_bool(str_val):
    if str_val == "true":
        return True
    return False

def not_inst(args, data_frames):
    if args[0].arg_type != "var":
        print("first argument must be a var")
        exit(55)#TODO
    assigned_var = get_var(args[0], data_frames)
    result = None
    operands = unpack_args(args, data_frames)
    first_operand = operands[1]

    if first_operand.arg_type != "bool":
        print("argument must be bool")
        exit(32)  # TODO

    if first_operand.value == "false":
        result = "true"
    if first_operand.value == "true":
        result = "false"

    assigned_var.value = result
    assigned_var.arg_type = "bool"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", nargs=1, help="help")
    ap.add_argument("--input", nargs=1, help="help")

    args = vars(ap.parse_args())

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

if __name__ == "__main__":
    main()


def tokenize(string):
    for l in ["{","}",":",";","#"]:
        string = string.replace(l," "+l+" ")
    return string.split()
    
def blockify(toks):
    name = ""
    brack = False
    block,line = [],[]
    blocks = {}
    for t in toks:
        if t == "{":
            brack = True
        elif t == "}" and brack == True:
            blocks[name] = block
            block = []
            brack = False
        elif brack:
            if t == ";":
                if line[0] != "#":
                    block.append([line[0],"".join(line[1:])])
                line = []
            elif t not in [":","="]:
                line.append(t)
        elif not brack:
            name = t
    return blocks

def execute(string="",style={}):
    blocks = blockify(tokenize(string))
    for block in blocks:
        for line in blocks[block]:
            if block != "body":
                style['-'.join([block,line[0]])] = line[1]
            else:
                style[line[0]] = line[1]

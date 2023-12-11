import utils


def filter_file_path(path):
    return "d3d11" in path or "xr" in path or "loader" in path


def filter_symbol(symbol):
    if symbol.kind == "const":
        return symbol.name.startswith("XR_")
    elif symbol.kind == "struct" or symbol.kind == "enum":
        return symbol.name.startswith("Xr")
    else:
        return False


def rename_symbol(symbol):
    if symbol.kind == "const":
        symbol.name = symbol.name[3:]
    elif symbol.kind == "struct":
        if symbol.name.startswith("vk"):
            symbol.name = "vk." + symbol.name[2:]
        else:
            symbol.name = symbol.name[2:]

        for field in symbol.fields:
            field.name = utils.to_snake_case(field.name)
    elif symbol.kind == "enum":
        prefix = ""

        if symbol.name == "XrStructureType":
            prefix = "XR_TYPE"
        else:
            for i, char in enumerate(symbol.name):
                if i == 0:
                    prefix += char.upper()
                    continue

                if char.isupper() and symbol.name[i - 1].islower():
                    prefix += "_"
                prefix += char.upper()

        for variant in symbol.variants:
            if variant.name.startswith(prefix):
                variant.name = variant.name[len(prefix) + 1 :]
            elif variant.name.startswith("XR_"):
                variant.name = variant.name[3:]
            else:
                variant.name = variant.name

        symbol.name = symbol.name[2:]

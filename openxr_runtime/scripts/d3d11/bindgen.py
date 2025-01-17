import utils


def filter_file_path(path):
    return "d3d" in path or "dxgi" in path


def filter_symbol(sym):
    if sym.kind == "func":
        return True
    elif sym.kind == "struct":
        return sym.name.startswith(("D3D11_", "ID3D11", "DXGI_", "IDXGI"))
    elif sym.kind == "enum":
        return sym.name.startswith(("D3D_", "D3D11_", "DXGI_"))
    elif sym.kind == "const":
        return sym.name.startswith("DXGI_") and not sym.name.startswith("DXGI_DEBUG_")
    else:
        return False


def rename_symbol(sym):
    if sym.kind == "func":
        sym.name = utils.to_snake_case(sym.name)
    elif sym.kind == "struct":
        if sym.name.startswith("D3D11_"):
            sym.name = utils.to_pascal_case(sym.name[6:])
        elif sym.name.startswith("ID3D11"):
            sym.name = sym.name[6:]
        elif sym.name.startswith("DXGI_"):
            sym.name = "DXGI" + utils.to_pascal_case(sym.name[5:])
        elif sym.name.startswith("IDXGI"):
            sym.name = "DXGI" + sym.name[5:]

        for field in sym.fields:
            if field.name == "lpVtbl":
                field.name = "vtable"
                continue
        
            if len(field.name) > 0:
                field.name = utils.to_snake_case(field.name)
    elif sym.kind == "enum":
        if sym.name == "D3D11_STANDARD_MULTISAMPLE_QUALITY_LEVELS":
            prefix = "D3D11_"
        elif sym.name == "D3D11_SHADER_MIN_PRECISION_SUPPORT":
            prefix = "D3D11_SHADER_MIN_PRECISION_"
        elif sym.name == "D3D11_TILED_RESOURCES_TIER":
            prefix = "D3D11_TILED_RESOURCES_"
        elif sym.name == "D3D11_CONSERVATIVE_RASTERIZATION_TIER":
            prefix = "D3D11_CONSERVATIVE_RASTERIZATION_"
        elif sym.name == "D3D11_AUTHENTICATED_PROCESS_IDENTIFIER_TYPE":
            prefix = "D3D11_PROCESSIDTYPE_"
        else:
            prefix = sym.name + "_"
                
            for suffix in ("_FLAG", "_FLAGS", "_MODE", "_FUNC", "_CLASSIFICATION", "_TYPE"):
                if sym.name.endswith(suffix):
                    prefix = sym.name[:-len(suffix) + 1]
                    break
        
        if sym.name.startswith("D3D_"):
            sym.name = utils.to_pascal_case(sym.name[4:])
        elif sym.name.startswith("D3D11_"):
            sym.name = utils.to_pascal_case(sym.name[6:])
        elif sym.name.startswith("DXGI_"):
            sym.name = "DXGI" + utils.to_pascal_case(sym.name[5:])
        
        for variant in sym.variants:
            if variant.name.startswith(prefix):
                variant.name = variant.name[len(prefix):]
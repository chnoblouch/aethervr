import utils


def filter_file_path(path):
    return "d3d11" in path or "dxgi" in path


def filter_symbol(sym):
    if sym.kind == "func":
        return sym.name == "CreateDXGIFactory"
    if sym.kind == "struct":
        return sym.name.startswith(("D3D11_", "ID3D11", "DXGI_", "IDXGI"))
    elif sym.kind == "enum":
        return sym.name.startswith(("D3D11_", "DXGI_"))
    else:
        return False


def rename_symbol(sym):
    if sym.kind == "func":
        if sym.name == "CreateDXGIFactory":
            sym.name = "create_dxgi_factory"
    if sym.kind == "struct":
        if sym.name.startswith("D3D11_"):
            sym.name = utils.to_pascal_case(sym.name[6:])
        elif sym.name.startswith("ID3D11"):
            sym.name = sym.name[6:]
        elif sym.name.startswith("DXGI_"):
            sym.name = "DXGI" + utils.to_pascal_case(sym.name[5:])
        elif sym.name.startswith("IDXGI"):
            sym.name = "DXGI" + sym.name[5:]

        for field in sym.fields:
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
        
        if sym.name.startswith("D3D11_"):
            sym.name = utils.to_pascal_case(sym.name[6:])
        elif sym.name.startswith("DXGI_"):
            sym.name = "DXGI" + utils.to_pascal_case(sym.name[5:])
        
        for variant in sym.variants:
            if variant.name.startswith(prefix):
                variant.name = variant.name[len(prefix):]
import platform


is_windows = platform.system() == "Windows"
is_linux = platform.system() == "Linux"


def banjo_target_name() -> str:
    if is_windows:
        return "x86_64-windows-msvc"
    elif is_linux:
        return "x86_64-linux-gnu"
    else:
        return "unknown"

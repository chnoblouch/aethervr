import platform


is_windows = platform.system() == "Windows"
is_linux = platform.system() == "Linux"
is_macos = platform.system() == "Darwin"


def banjo_target_name() -> str:
    if is_windows:
        return "x86_64-windows-msvc"
    elif is_linux:
        return "x86_64-linux-gnu"
    elif is_macos:
        return "aarch64-macos"
    else:
        return "unknown"

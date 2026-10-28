class TerminalColours:
    # --- 1-8: Modifiers & Resets ---
    reset = '\033[0m'
    bold = '\033[1m'
    dim = '\033[2m'
    italic = '\033[3m'
    underline = '\033[4m'
    blink = '\033[5m'
    reverse = '\033[7m'
    hidden = '\033[8m'

    # --- 9-16: Standard Foreground Colors ---
    black = '\033[30m'
    red = '\033[31m'
    green = '\033[32m'
    yellow = '\033[33m'
    blue = '\033[34m'
    magenta = '\033[35m'
    cyan = '\033[36m'
    white = '\033[37m'

    # --- 17-24: Bright Foreground Colors ---
    brightBlack = '\033[90m'
    brightRed = '\033[91m'
    brightGreen = '\033[92m'
    brightYellow = '\033[93m'
    brightBlue = '\033[94m'
    brightMagenta = '\033[95m'
    brightCyan = '\033[96m'
    brightWhite = '\033[97m'

    # --- 25-32: Combined Bold & Dim Style Shortcuts ---
    boldRed = '\033[1m\033[31m'
    boldGreen = '\033[1m\033[32m'
    boldYellow = '\033[1m\033[33m'
    boldBlue = '\033[1m\033[34m'
    boldCyan = '\033[1m\033[36m'
    dimRed = '\033[2m\033[31m'
    dimGreen = '\033[2m\033[32m'
    dimBlue = '\033[2m\033[34m'
    
def printC(message: str, *styleNames: str):
    combinedCode = ""
    for styleName in styleNames:
        # Dynamically fetch the ANSI code from TerminalColors class using getattr()
        ansiCode = getattr(TerminalColours, styleName, "")
        combinedCode += ansiCode

    print(f"{combinedCode}{message}{TerminalColours.reset}")
# ansi colorizer

class Colorizer:
    def __init__(self):
        self.colors = {
            'black': '\033[30m',
            'red': '\033[31m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'magenta': '\033[35m',
            'cyan': '\033[36m',
            'white': '\033[37m',
            'reset': '\033[0m'
        }

    def colorize(self, text, color):
        return self.colors[color] + text + self.colors['reset']

    def colorize_list(self, text, color):
        return [self.colors[color] + t + self.colors['reset'] for t in text]

    def colorize_dict(self, text, color):
        return {k: self.colors[color] + v + self.colors['reset'] for k, v in text.items()}
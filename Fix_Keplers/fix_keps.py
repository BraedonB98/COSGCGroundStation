import re
from tempfile import mkstemp
from shutil import move
from os import fdopen, remove


def fix_keps():
    file_path = "C:/Users/COSGC/AppData/Roaming/SatPC32/Kepler/weather.txt"
    fh, abs_path = mkstemp()
    with fdopen(fh,'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                new_line = re.sub(r'(AA )|(AA-)', 'AA', line)
                new_file.write(re.sub(r'METEOR-M ', 'METEOR', new_line))
    remove(file_path)
    move(abs_path, file_path)

if __name__ == "__main__":
    fix_keps()

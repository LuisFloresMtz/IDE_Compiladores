import subprocess


class CompilerRunner:
    def __init__(self, compiler_path="compiler.exe"):
        self.compiler_path = compiler_path

    def run_phase(self, phase, source_file):
        """
        phase: lexico | sintactico | semantico | intermedio | ejecutar
        source_file: ruta del archivo de código
        """

        try:
            result = subprocess.run(
                [self.compiler_path, phase, source_file],
                capture_output=True,
                text=True
            )

            output = result.stdout
            errors = result.stderr

            return output, errors

        except Exception as e:
            return "", f"Error ejecutando compilador: {str(e)}"

from dotenv import load_dotenv
import typer

load_dotenv()

def main():
    typer.echo("Hello World")


if __name__ == "__main__":
    typer.run(main)
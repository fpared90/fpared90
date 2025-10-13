import os
import sys

# Run both as a package module and as a standalone script
if __package__:
    from .app import main  # type: ignore
else:
    sys.path.append(os.path.dirname(__file__))
    from app import main  # type: ignore

if __name__ == '__main__':
    main()

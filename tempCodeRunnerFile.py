if key == b'\x1b':  # ESC
      glutDestroyWindow(glutGetWindow())
      sys.exit()
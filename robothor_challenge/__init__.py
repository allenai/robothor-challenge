from robothor_challenge.startx import startx
class RobothorChallenge:

    def __init__(tasks):
        setup_env()
        pass

    def setup_env(self):
        xthread = threading.Thread(target=startx)
        xthread.daemon = True
        xthread.start()

if __name__ == '__main__':
    c = RobothorChallenge()
    import time
    time.sleep()


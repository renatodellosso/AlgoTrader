from multiprocessing import Process


def test():
    print("This is a test")

if __name__ == "__main__":
    print("Starting process...")
    process = Process(target=test)
    process.start()
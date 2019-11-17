from knockknock.desktop_sender import desktop_sender


@desktop_sender(title="test")
def train():
    import time
    time.sleep(10)
    return {"loss":1}

train()
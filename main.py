from gfwfucker import GFWFuckerServer
from asyncio import run

if __name__ == '__main__':
    from gfwfucker.config import *
    run(GFWFuckerServer(TEST_SERVER, TEST_PORT, TEST_PASSWORD).run())

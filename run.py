if __name__ == '__main__':
    from mmr_database.mmrDB import mmrDB
    import sys

    arg1 = bool(int(sys.argv[1]))
    mmrDB(DOWNLOAD_DB=arg1)

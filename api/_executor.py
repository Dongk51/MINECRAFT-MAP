from concurrent.futures import ThreadPoolExecutor

# max_workers=1: serialize world operations to prevent concurrent file corruption
executor = ThreadPoolExecutor(max_workers=1)

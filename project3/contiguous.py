import math
import timeit

directory = [0]*32768
DT = []
block_number = 32768
BLOCK_SIZE = 0

create_time = 0.0
access_time = 0.0
extend_time = 0.0
shrink_time = 0.0


def create_table(file_id, file_length):
    # timer to calculate run time of the function
    global create_time
    start = timeit.default_timer()
    # block length of the file
    num_block = math.ceil(file_length / BLOCK_SIZE)
    counter = 0
    defragmentation_counter = 0
    first_empty = 0

    for index, block in enumerate(directory):  # contiguous
        if block == 0:
            counter += 1
            defragmentation_counter += 1
            if counter == 1:
                # first empty block index
                first_empty = index
        else:
            counter = 0
        # if counter (empty block number in the directory) is equal to number of block that created file has
        if counter == num_block:
            elt = {
                "file_id": file_id,
                "starting_index": index - num_block + 1,
                "file_length": file_length
            }
            DT.append(elt)
            # make 1 to directory's empty blocks after file is created contiguously
            directory[elt["starting_index"]: elt["starting_index"] + num_block] = [1] * num_block
            # time stopper
            stop = timeit.default_timer()
            create_time += stop - start
            return num_block
        # if there is no enough space for normal contiguous creation, do defragmentation first to create the file
        # if there is enough empty blocks that are not side by side, do defragmentation to create the file contiguously
        elif defragmentation_counter == num_block:
            flag = False
            last_empty = index
            # range between first empty index and last index that we found enough empty block
            # that is the size of the file in terms of blocks to create the file
            block_range = index - first_empty + 1
            while block_range >= num_block:
                # loop from the first empty block index to last empty block index
                for i, entry in enumerate(directory[first_empty:(last_empty + 1)], start=first_empty):
                    if flag:
                        break
                    # if entry is full
                    if entry == 1:
                        for file in DT:
                            # if i equals file starting index
                            if i == file["starting_index"]:
                                flag = True
                                # set file (file that will be shifted) starting index to the first empty index
                                file["starting_index"] = first_empty
                                file_block = math.ceil(file["file_length"] / BLOCK_SIZE)
                                # new first empty index is the next empty index
                                # after the file block length added to its new starting index
                                # since we are shifting files from the beginning to the left
                                first_empty += file_block
                                block_range -= file_block
                                break
                else:
                    break
            else:
                # update directory after created the file
                for i, entry in enumerate(directory[first_empty:(index + 1)], start=first_empty):
                    directory[i] = 1
                # add file to DT
                elt = {
                    "file_id": file_id,
                    "starting_index": index - num_block + 1,
                    "file_length": file_length
                }
                DT.append(elt)
                stop = timeit.default_timer()
                create_time += stop - start
                return num_block
    stop = timeit.default_timer()
    create_time += stop - start
    return -1


def access(file_id, byte_offset):
    global access_time
    start = timeit.default_timer()
    for file in DT:
        starting_index = file["starting_index"]
        if file_id == file["file_id"]:
            # if byte offset bigger than the file length, it is not possible to access
            if byte_offset > file["file_length"]:
                stop = timeit.default_timer()
                access_time += stop - start
                return -1
            if starting_index == 0:
                stop = timeit.default_timer()
                access_time += stop - start
                return byte_offset
            # calculated the byte that we want to reach
            result = (starting_index - 1) * BLOCK_SIZE + byte_offset
            stop = timeit.default_timer()
            access_time += stop - start
            return result
    stop = timeit.default_timer()
    access_time += stop - start
    return -1


# extension is in terms of number of blocks
def extend(file_id, extension):
    global block_number
    global extend_time
    start = timeit.default_timer()
    first_empty = 0
    success = False
    count = 0
    for index, file in enumerate(DT):
        if file_id == file["file_id"]:
            n_block = math.ceil(file["file_length"] / BLOCK_SIZE)
            starting_index = file["starting_index"]
            last_block_index = starting_index + n_block - 1
            no_need_for_compaction = False
            enough_space_counter = 0
            for i, is_full in enumerate(directory[(last_block_index + 1):], start=last_block_index + 1):
                if is_full != 1:
                    enough_space_counter += 1
                    # If there exist space side by side to extend, no need for compaction
                    if enough_space_counter == extension:
                        no_need_for_compaction = True
                        break
                else:
                    no_need_for_compaction = False
                    break
            if no_need_for_compaction:
                counter = extension
                # make directory's blocks 1 for each extended block
                for a, is_full in enumerate(directory[(last_block_index + 1):], start=last_block_index + 1):
                    if counter != 0:
                        counter -= 1
                        directory[a] = 1
                    else:
                        break
                # update file length
                file["file_length"] = file["file_length"] + (extension * BLOCK_SIZE)
                stop = timeit.default_timer()
                extend_time += stop - start
                return extension
            # we need to do compaction first, same logic as I did in create defragmentation applied here as well
            else:
                # get the last block of the file that we want to extend
                last_block = math.ceil(file["file_length"] / BLOCK_SIZE) + starting_index - 1
                empty_block = 0
                # loop through starting from last block index of the file + 1 till extension to see
                # whether there are any consecutive empty blocks (less than the extension) to extend the file
                for i, entry in enumerate(directory[(last_block + 1):(last_block + extension + 1)],
                                          start=last_block + 1):
                    # if there is empty block in the directory, increment empty block count by 1
                    if entry == 0:
                        empty_block += 1
                    # when directory entry is not 0, break. In this way, we can find
                    # the number of consecutive empty blocks if there are any
                    else:
                        break
                # loop through to see whether there are any empty blocks before the file starting index
                for i, entry in enumerate(directory[:(starting_index + 1)], start=0):
                    if entry == 0:
                        count += 1
                    # take into account empty blocks located back or in front of the file that we want to extend
                    if count == extension - empty_block:
                        block_empty = 0
                        # to do compaction, we need to loop backwards
                        # to shift the files located back of the file that we want to extend
                        for b in range(starting_index, 0, -1):
                            if directory[b] == 0:
                                block_empty += 1
                            if block_empty == count:
                                first_empty = b
                                flag = False
                                # while extension equal or larger to count (number of empty blocks)
                                while extension >= count:
                                    # loop from the first empty block index to starting index of the file
                                    # (blocks before the file's starting index)
                                    for ii, block in enumerate(directory[first_empty:(starting_index + 1)],
                                                               start=first_empty):
                                        if flag:
                                            break
                                        if block == 1:
                                            for f in DT:
                                                if ii == f["starting_index"]:
                                                    flag = True
                                                    # count is the range that we need to do extension
                                                    # in every iteration we are updating it since one shift is done
                                                    # and we need to add how many number of shift is made to the count
                                                    # till range become larger than extension
                                                    count += (f["starting_index"] - first_empty)
                                                    # set file starting index (file that will be shifted)
                                                    # to the first empty index
                                                    f["starting_index"] = first_empty
                                                    file_block = math.ceil(f["file_length"] / BLOCK_SIZE)
                                                    # new first empty index is the next empty index
                                                    # after the file block length added to its new starting index
                                                    # since we are shifting files from the beginning to the left
                                                    first_empty += file_block
                                                    break
                                    else:
                                        break
                                else:
                                    success = True
                                    break
            if success:
                # file's last index after it is extended
                last_index = last_block_index + extension - count
                # update the directory
                for iii, block in enumerate(directory[first_empty:(last_index + 1)], start=0):
                    directory[iii] = 1
                file["file_length"] = file["file_length"] + (extension * BLOCK_SIZE)
                stop = timeit.default_timer()
                extend_time += stop - start
                return extension
    stop = timeit.default_timer()
    extend_time += stop - start
    return -1


# shrinking in terms of blocks
def shrink(file_id, shrinking):
    global block_number
    global shrink_time
    start = timeit.default_timer()
    for index, file in enumerate(DT):
        if file_id == file["file_id"]:
            num_block = math.ceil(file["file_length"] / BLOCK_SIZE)
            # if shrinking equal or larger than num_block (block number of a file), shrink is not possible
            if num_block <= shrinking:
                stop = timeit.default_timer()
                shrink_time += stop - start
                return -1
            else:
                # calculate new file length
                file["file_length"] = file["file_length"] - (shrinking * BLOCK_SIZE)
                # update directory
                for i, block in enumerate(directory):
                    if num_block - shrinking <= i <= num_block - 1:
                        directory[i] = 0
                stop = timeit.default_timer()
                shrink_time += stop - start
                return shrinking
    stop = timeit.default_timer()
    shrink_time += stop - start
    return -1


def main():
    global BLOCK_SIZE
    global block_number
    global DT
    global directory
    file_id = 0

    c_average = 0.0
    a_average = 0.0
    e_average = 0.0
    sh_average = 0.0

    files = ['input_1024_200_9_0_9.txt', 'input_1024_200_9_0_0.txt',
             'input_2048_600_5_5_0.txt', 'input_8_600_5_5_0.txt', 'input_1024_200_5_9_9.txt']

    for file in files:
        file_path = "./io/" + file
        DT = []
        block_number = 32768
        directory = [0] * block_number
        BLOCK_SIZE = 0
        # 1 for success, 2 for reject
        a_count_1 = 0
        a_count_2 = 0
        c_count_1 = 0
        c_count_2 = 0
        e_count_1 = 0
        e_count_2 = 0
        sh_count_1 = 0
        sh_count_2 = 0
        with open(file_path, "r") as a_file:
            BLOCK_SIZE = int(a_file.name.strip().rsplit('_')[1])
            counter = 0
            for line in a_file:
                counter += 1
                stripped_line = line.strip()
                if stripped_line[0] == 'c':
                    file_length = int(stripped_line.rsplit(':')[1])
                    num_block = create_table(file_id, file_length)
                    if num_block != -1:
                        block_number -= num_block
                        file_id += 1
                        c_count_1 += 1
                    else:
                        c_count_2 += 1
                elif stripped_line[0] == 'a':
                    file_id_for_access = int(stripped_line.rsplit(':')[1])
                    byte_offset = int(stripped_line.rsplit(':')[2])
                    directory_address = access(file_id_for_access, byte_offset)
                    if directory_address != -1:
                        a_count_1 += 1
                    else:
                        a_count_2 += 1
                elif stripped_line[0] == 's':
                    file_id_for_shrink = int(stripped_line.rsplit(':')[1])
                    shrink_block = int(stripped_line.rsplit(':')[2])
                    shrink_result = shrink(file_id_for_shrink, shrink_block)
                    if shrink_result != -1:
                        block_number += shrink_block
                        sh_count_1 += 1
                    else:
                        sh_count_2 += 1
                elif stripped_line[0] == 'e':
                    file_id_for_extend = int(stripped_line.rsplit(':')[1])
                    extension = int(stripped_line.rsplit(':')[2])
                    if extension <= block_number:
                        extension_block = extend(file_id_for_extend, extension)
                        if extension_block != -1:
                            block_number -= extension
                            e_count_1 += 1
                        else:
                            e_count_2 += 1
                    else:
                        e_count_2 += 1

        c_average += create_time / (c_count_1 + c_count_2)
        a_average += access_time / (a_count_1 + a_count_2)

        print("File name: ", file)
        print("\n")
        print("CREATED FILE NUMBER: ", c_count_1)
        print("CREATE REJECTED FILE NUMBER: ", c_count_2)
        print("create time: ", create_time / (c_count_1 + c_count_2))
        print("ACCESSED FILE NUMBER: ", a_count_1)
        print("ACCESS REJECTED FILE NUMBER: ", a_count_2)
        print("access time: ", access_time / (a_count_1 + a_count_2))
        if e_count_1 + e_count_2 != 0:
            print("EXTENDED FILE NUMBER: ", e_count_1)
            print("EXTEND REJECTED FILE NUMBER: ", e_count_2)
            print("extend time: ", extend_time / (e_count_1 + e_count_2))
            e_average += extend_time / (e_count_1 + e_count_2)
        else:
            print("EXTENDED FILE NUMBER: ", e_count_1)
            print("EXTEND REJECTED FILE NUMBER: ", e_count_2)
        if sh_count_1 + sh_count_2 != 0:
            print("SHRUNK FILE NUMBER: ", sh_count_1)
            print("SHRINK REJECTED FILE NUMBER: ", sh_count_2)
            print("shrink time: ", shrink_time / (sh_count_1 + sh_count_2))
            sh_average += shrink_time / (sh_count_1 + sh_count_2)
        else:
            print("SHRUNK FILE NUMBER: ", sh_count_1)
            print("SHRINK REJECTED FILE NUMBER: ", sh_count_2)
        print("\n")

    print("Average create time: ", c_average / 5)
    print("Average access time: ", a_average / 5)
    print("Average extend time: ", e_average / 5)
    print("Average shrink time: ", sh_average / 5)


if __name__ == "__main__":
    main()
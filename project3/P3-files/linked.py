import math
import timeit

block_number = 32768
directory = [0]*block_number
FAT = [-2]*block_number
DT = []
BLOCK_SIZE = 0
FAT_EXTRA_BYTE = 4

create_time = 0.0
access_time = 0.0
extend_time = 0.0
shrink_time = 0.0


def create_table(file_id, file_length):
    # returns number of blocks of the file that is used to subtract from blocks_in_directory after completion,
    # if there is no space in the directory to create that file it returns -1.
    # even though this is linked allocation, if there is enough contiguous space, it allocates the files in a
    # contiguous manner.
    # it does not randomly places the blocks of the file in directory. It checks the empty blocks in increasing order
    # and it allocates the blocks in increasing order.
    global create_time
    start = timeit.default_timer()
    num_block = math.ceil(file_length / BLOCK_SIZE)
    # FAT 4 bytes included
    num_block = math.ceil((file_length + FAT_EXTRA_BYTE * num_block) / BLOCK_SIZE)

    starting_index = 0
    # FAT[prev_index] will be set to -1 at the end, to indicate the end of the file
    prev_index = -1
    # holds the empty block number
    counter = 0
    # if counter (number of empty block in the directory) is less than file block
    while counter < num_block:
        for index, block in enumerate(directory[prev_index + 1:], start=prev_index + 1):
            if block == 0:
                counter += 1
                directory[index] = 1
                if counter == 1:
                    starting_index = index
                else:
                    FAT[prev_index] = index
                prev_index = index
                break
        # Rollback part for FAT. Since we are moving putting the pointer for the next index to FAT,
        # if empty block exists, than, if there are no space in the directory afterwards (no 1 anymore),
        # we need to do rollback. We need to remove all the pointers put previously and make them -2 again.
        else:
            directory[prev_index] = 0
            counter -= 1
            prev_prev_index = -2
            for index, next_index in enumerate(FAT):
                if next_index == prev_index:
                    prev_prev_index = index
            if prev_prev_index != -2:
                while counter != 0:
                    FAT[prev_prev_index] = -2
                    directory[prev_prev_index] = 0
                    for index, next_index in enumerate(FAT):
                        if next_index == prev_prev_index:
                            prev_prev_index = index
                            counter -= 1
                            break
                    else:
                        break
                FAT[prev_prev_index] = -2
            break
    else:
        # set FAT index (file's last index) to -1 (file ended here)
        FAT[prev_index] = -1
        elt = {
            "file_id": file_id,
            "starting_index": starting_index,
            "file_length": file_length
        }
        # add file to the DT
        DT.append(elt)
        stop = timeit.default_timer()
        create_time += stop - start
        return num_block
    stop = timeit.default_timer()
    create_time += stop - start
    return -1


# this method updates directory and FAT recursively.
def recursive_extend(extension, counter, prev_index, list_index):
    # this is the extension part, if it can make it extension number of times, returns 0.
    if extension == 0:
        FAT[prev_index] = -1
        return 0
    for index, block in enumerate(directory[list_index+1:], start=list_index+1):  # ll
        if block == 0:
            FAT[prev_index] = index
            directory[index] = 1
            return recursive_extend(extension - 1, counter + 1, index, index)
    directory[prev_index] = 0
    counter -= 1
    prev_prev_index = -2
    for index, next_index in enumerate(FAT):
        if next_index == prev_index:
            prev_prev_index = index
    if prev_prev_index != -2:
        while counter != 0:
            FAT[prev_prev_index] = -2
            directory[prev_prev_index] = 0
            for index, next_index in enumerate(FAT):
                if next_index == prev_prev_index:
                    prev_prev_index = index
                    counter -= 1
                    break
            else:
                break
        FAT[prev_prev_index] = -1


# returns directory address of that byte, and returns -1 if cannot access to that byte in the file.
# by using the pointers in FAT, this method goes to the requested block by going block by block in FAT.
def access(file_id, byte_offset):
    global access_time
    start = timeit.default_timer()
    block_that_has_byte = math.ceil(byte_offset / BLOCK_SIZE)
    for file in DT:
        starting_index = file["starting_index"]
        if file_id == file["file_id"]:
            # if byte offset bigger than the file length, it is not possible to access
            if byte_offset > file["file_length"]:
                stop = timeit.default_timer()
                access_time += stop - start
                return -1
            index = starting_index
            pointer = index
            prev_of_last_pointer = index
            for i in range(block_that_has_byte - 1):
                if pointer != -1 and pointer != -2:
                    prev_of_last_pointer = pointer
                    pointer = FAT[pointer]
                else:
                    pointer = prev_of_last_pointer
            if block_that_has_byte == 1:
                result = byte_offset
            else:
                # calculated the byte that we want to reach
                result = (pointer - 1) * BLOCK_SIZE + byte_offset - ((block_that_has_byte - 1) * BLOCK_SIZE)
            stop = timeit.default_timer()
            access_time += stop - start
            return result
    stop = timeit.default_timer()
    access_time += stop - start
    return -1


def extend(file_id, extension):
    # returns the number of blocks that is extended with taking into account the pointer size of FAT, in the main,
    # I subtract this from the total available block number (blocks_in_directory). If cannot extend it returns -1.
    # like in create operation it allocates the blocks in both directory and FAT in increasing order. First, checks if
    # there is enough space in memory to perform extension, if there is, then starts extending after the last block
    # index of the file to be extended, if it goes to the very end of the directory filling blocks,
    # it starts again from the beginning of the directory.
    global block_number
    global extend_time
    start = timeit.default_timer()
    for index, file in enumerate(DT):
        if file_id == file["file_id"]:
            n_block = math.ceil(file["file_length"] / BLOCK_SIZE)
            total_bytes = file["file_length"] + n_block * FAT_EXTRA_BYTE
            n_block_initial = math.ceil(total_bytes / BLOCK_SIZE)
            if block_number >= extension:
                starting_index = file["starting_index"]
                prev_index = starting_index
                last_block_index = 0
                while prev_index != -1:
                    last_block_index = prev_index
                    prev_index = FAT[prev_index]
                # updates directory and FAT
                recursive_extend(extension, 0, last_block_index, -1)
                total_bytes_final = file["file_length"] + (BLOCK_SIZE * extension) + (extension * FAT_EXTRA_BYTE)
                n_block_end = math.ceil(total_bytes_final / BLOCK_SIZE)
                # I took the pointer sizes into account and calculated first how many bytes should be decreased from the
                # total memory and then converted it to block type. And in the main method, I decreased this block
                # number from current available blocks_in_directory
                n_block_final = n_block_end - n_block_initial
                file["file_length"] = file["file_length"] + extension * BLOCK_SIZE
                stop = timeit.default_timer()
                extend_time += stop - start
                return n_block_final
    stop = timeit.default_timer()
    extend_time += stop - start
    return -1


def shrink(file_id, shrinking):
    # returns the number of blocks that is shrunk with taking into account the pointer size of FAT, in the main,
    # I add this to the total available blocks_in_directory. If cannot shrink it returns -1.
    # by using the information of FAT holding -1 at the end of the file, it goes to the end block of the file first,
    # then starts removing the blocks by starting from the last block and going in reversed order exactly shrinking
    # times using the pointers of FAT to go back.
    global shrink_time
    start = timeit.default_timer()
    # since I remove shrinking as I remove blocks I hold the original value here
    original_shrinking = shrinking
    for index, file in enumerate(DT):
        if file_id == file["file_id"]:
            n_block = math.ceil(file["file_length"] / BLOCK_SIZE)
            total_bytes = file["file_length"] + n_block * FAT_EXTRA_BYTE
            n_block_initial = math.ceil(total_bytes / BLOCK_SIZE)
            if n_block <= shrinking:
                stop = timeit.default_timer()
                shrink_time += stop - start
                return -1
            # if file has enough blocks to shrink, and not to be deleted entirely.
            else:
                starting_index = file["starting_index"]
                prev_index = starting_index
                last_block_index = 0
                # for going to the end of the file
                while prev_index != -1:
                    last_block_index = prev_index
                    prev_index = FAT[prev_index]
                # when we reach the end pointer_index = -1
                prev_prev_index = last_block_index
                # removing process until shrinking == 0
                while (shrinking > 0) and (prev_prev_index != -1):
                    shrinking -= 1
                    FAT[prev_prev_index] = -2
                    directory[prev_prev_index] = 0
                    for i, next_index in enumerate(FAT):
                        if next_index == prev_prev_index:
                            prev_prev_index = i
                            break
                    else:
                        prev_prev_index = -1
                        break
                FAT[prev_prev_index] = -1
                # to decrease the number of blocks from the memory, I first calculate how many byte should be decreased
                # considering the FAT pointer sizes, and then convert bytes back to that blocks.
                total_bytes_final = file["file_length"] - (BLOCK_SIZE * original_shrinking) - \
                                    (original_shrinking * FAT_EXTRA_BYTE)
                n_block_end = math.ceil(total_bytes_final / BLOCK_SIZE)
                n_block_final = n_block_initial - n_block_end
                file["file_length"] = file["file_length"] - (original_shrinking * BLOCK_SIZE)
                stop = timeit.default_timer()
                shrink_time += stop - start
                return n_block_final
    stop = timeit.default_timer()
    shrink_time += stop - start
    return -1


def main():
    global BLOCK_SIZE
    global block_number
    global DT
    global directory
    global FAT
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
        FAT = [-2] * block_number
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
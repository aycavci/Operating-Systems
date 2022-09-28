import math

directory = [0]*32768
FAT = [-2]*32768
DT = []
block_number = 32768
BLOCK_SIZE = 0
FAT_EXTRA_BYTE = 4


def create_table(file_id, file_length):
    num_block = math.ceil(file_length / BLOCK_SIZE)
    counter = 0

    for index, block in enumerate(directory):  # contiguous
        if block == 0:
            counter += 1
        else:
            counter = 0
        if counter == num_block:
            elt = {
                "file_id": file_id,
                "starting_index": index - num_block + 1,
                "file_length": file_length
            }
            DT.append(elt)
            directory[elt["starting_index"]: elt["starting_index"] + num_block] = [1] * num_block
            return num_block

    print("Couldn't allocate with contiguous")

    num_block = math.ceil((file_length + FAT_EXTRA_BYTE * num_block) / BLOCK_SIZE)

    starting_index = -1
    prev_index = -1
    counter = 0
    while counter < num_block:
        for index, block in enumerate(directory[prev_index + 1:], start=prev_index + 1):
            if block == 0:
                counter += 1
                if counter == 1:
                    starting_index = index
                else:
                    FAT[prev_index] = index
                prev_index = index
                break
        else:
            prev_prev_index = -1
            for index, next_index in enumerate(FAT):
                if next_index == prev_index:
                    prev_prev_index = index
            if prev_prev_index != -1:
                while prev_prev_index != -1:
                    FAT[prev_prev_index] = -2
                    for index, next_index in enumerate(FAT):
                        if next_index == prev_prev_index:
                            prev_prev_index = index
                            break
                    else:
                        prev_prev_index = -1
            break
    else:
        FAT[prev_index] = -1
        index = starting_index
        directory[index] = 1
        while FAT[index] != -1:
            next_index = FAT[index]
            directory[next_index] = 1
            index = next_index
        elt = {
            "file_id": file_id,
            "starting_index": starting_index,
            "file_length": file_length
        }
        DT.append(elt)
        print("linked done")
        return num_block
    return -1

    # num_block = math.ceil(file_length + FAT_EXTRA_BYTE * num_block / BLOCK_SIZE)
    # starting_index = recursive_ll(num_block, 0, -1, -1, -1)
    #
    # if starting_index != -1:
    #     index = starting_index
    #     directory[index] = 1
    #     while FAT[index] != -1:
    #         next_index = FAT[index]
    #         directory[next_index] = 1
    #         index = next_index
    #     elt = {
    #         "file_id": file_id,
    #         "starting_index": starting_index,
    #         "file_length": file_length
    #     }
    #     DT.append(elt)
    #     print("Linked done")
    #     return num_block
    # return -1


def recursive_ll(n_b, counter, prev_index, starting_index, list_index):
    if counter == n_b:
        FAT[prev_index] = -1
        return starting_index
    for index, block in enumerate(directory[list_index+1:], start=list_index+1):  # ll
        if block == 0:
            counter += 1
            if counter == 1:
                starting_index = index
            else:
                FAT[prev_index] = index
            return recursive_ll(n_b, counter, index, starting_index, index)
    prev_prev_index = -2
    for index, next_index in enumerate(FAT):
        if next_index == prev_index:
            prev_prev_index = index
    if prev_prev_index != -2:
        while prev_prev_index != -2:
            FAT[prev_prev_index] = -2
            for index, next_index in enumerate(FAT):
                if next_index == prev_prev_index:
                    prev_prev_index = index
                    break
            else:
                prev_prev_index = -2
    return -1

# [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
# [0, x, 0, x, 0, x, 0, x, x, x]
# create 5 block item


def access(file_id, byte_offset):
    block_that_has_byte = math.ceil(byte_offset / BLOCK_SIZE)
    index = -5
    for file in DT:
        starting_index = file["starting_index"]
        if file_id == file["file_id"]:
            if byte_offset > file["file_length"]:
                return "access request declined"
            index = starting_index
            file_length = file["file_length"]
            # means that it is contiguous allocation
            if FAT[index] == -2:
                result = (starting_index - 1) * BLOCK_SIZE + byte_offset
                print("C_ACCESSED file_id: ", file_id, " file_length: ",
                      file_length, " byte_offset: ", byte_offset, "directory: ", result,
                      "starting index: ", starting_index)
                return result
            # means that it is linked allocation
            else:
                pointer = FAT[index]
                for i in range(block_that_has_byte - 1):
                    pointer = FAT[pointer]

                result = (pointer - 1) * BLOCK_SIZE + byte_offset - ((block_that_has_byte - 1) * BLOCK_SIZE)
                print("L_ACCESSED file_id: ", file_id, " file_length: ",
                      file_length, " byte_offset: ", byte_offset)
                return result
    if index != -5:
        return "File not found!"

    # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    # [3, x, 5, x, 7, x, -1, x, x, x]
    # 1 3 5 7


# TODO: fat byte i hesaba kat
def extend(file_id, extension):  # extension is no. of blocks
    global block_number
    # print(directory)
    for index, file in enumerate(DT):
        if file_id == file["file_id"]:
            n_block = math.ceil(file["file_length"] / BLOCK_SIZE)
            if FAT[file["starting_index"]] == -2:  # cont. extend
                starting_index = file["starting_index"]
                last_block_index = starting_index + n_block - 1
                no_need_for_compaction = False
                enough_space_counter = 0
                for i, is_full in enumerate(directory[(last_block_index + 1):], start=last_block_index + 1):
                    if is_full != 1:
                        enough_space_counter += 1
                        if enough_space_counter == extension:  # there exist space to extend, no need for compaction
                            no_need_for_compaction = True
                            break
                    else:
                        no_need_for_compaction = False
                        break
                if no_need_for_compaction:
                    # print("file with file_id: ", file_id, " blocks to be extended: ", extension)
                    # print("last block index: ", last_block_index)
                    # print(directory)
                    counter = extension
                    for i, is_full in enumerate(directory[(last_block_index + 1):], start=last_block_index + 1):
                        if counter != 0:
                            counter -= 1
                            # print("im extended ", i - last_block_index, " times")
                            directory[i] = 1
                        else:
                            break
                    file["file_length"] = file["file_length"] + extension * BLOCK_SIZE
                    # print(directory)
                    return extension
                else:  # we need to do compaction here
                    print("we need to do compaction here")

                    return -1 # simdilik boyle
    for index, file in enumerate(DT):
        if file_id == file["file_id"]:
            n_block = math.ceil(file["file_length"] / BLOCK_SIZE)
            if FAT[file["starting_index"]] == -2:
                print("done")
            else:
                if block_number >= extension:
                    starting_index = file["starting_index"]
                    prev_index = starting_index
                    last_block_index = 0
                    while prev_index != -1:
                        last_block_index = prev_index
                        prev_index = FAT[prev_index]
                    print(FAT)
                    recursive_ll(extension+1, 1, last_block_index, -1, -1)
                    starting_index = directory.index(0)
                    if starting_index != -1:
                        index = starting_index
                        directory[index] = 1
                        while FAT[index] != -1:
                            next_index = FAT[index]
                            directory[next_index] = 1
                            index = next_index
                        file["file_length"] = file["file_length"] + extension * BLOCK_SIZE
                        print("Linked extend done!")
                        print(FAT)
                        return n_block
                    return -1


# TODO: fat byte i hesaba kat
def shrink(file_id, shrinking):
    global block_number
    # print(DT)
    for index, file in enumerate(DT):
        if file_id == file["file_id"]:
            n_block = math.ceil(file["file_length"] / BLOCK_SIZE)
            if n_block <= shrinking:
                return -1
            else:
                # cont
                if FAT[file["starting_index"]] == -2:
                    bytes_in_last_block = file["file_length"] % BLOCK_SIZE
                    file["file_length"] = file["file_length"] - (shrinking - 1) * BLOCK_SIZE - bytes_in_last_block
                    for i, block in enumerate(directory):
                        if n_block - shrinking + 1 <= i <= n_block:
                            directory[i] = 0
                    return shrinking
                # linked
                else:
                    bytes_in_last_block = file["file_length"] % BLOCK_SIZE
                    file["file_length"] = file["file_length"] - (shrinking - 1) * BLOCK_SIZE - bytes_in_last_block

                    starting_index = file["starting_index"]
                    prev_index = starting_index
                    last_block_index = 0
                    prev_prev_index = 0

                    for i, pointer in enumerate(FAT):
                        if i == starting_index:
                            for j in range(n_block + 1):
                                prev_prev_index = prev_index
                                prev_index = FAT[prev_index]
                                if prev_index == -1:
                                    last_block_index = prev_prev_index
                    for i, next_index in enumerate(FAT):
                        if next_index == FAT[last_block_index]:
                            prev_prev_index = i
                    while shrinking > 0 & prev_prev_index != -1:
                        shrinking -= 1
                        FAT[prev_prev_index] = -2
                        directory[prev_prev_index] = 0
                        for i, next_index in enumerate(FAT):
                            if next_index == prev_prev_index:
                                prev_prev_index = i
                                break
                        else:
                            prev_prev_index = -1
                    FAT[prev_prev_index] = -1
                    return shrinking

                    # yukardaki iki line da hata var muhtemelen

    # print(DT)
    # print(FAT)
    # print(directory)

    # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    # [3, x, 5, x, 7, x, -1, x, x, x]
    # 1 3 5 7 -1

    # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    # [3, x, 5, x, 7, x, -1, x, x, x]
    # [1, 0, 1, 0, 1, 0, 1, 0, 0, 0]
    # 1 3 5 7


# TODO: shrink ve extend de block number i update et!


def main():
    global BLOCK_SIZE
    global block_number
    file_id = 0

    # TODO: inputlari alma isi for loop ile yapilmali

    with open("./io/input_1024_200_5_9_9.txt", "r") as a_file:
        BLOCK_SIZE = int(a_file.name.strip().rsplit('_')[1])
        for line in a_file:
            stripped_line = line.strip()
            if stripped_line[0] == 'c':
                file_length = int(stripped_line.rsplit(':')[1])
                num_block = create_table(file_id, file_length)
                if num_block != -1:
                    block_number -= num_block
                    print("ADDED! file_id: ", file_id, " file_length: ", file_length)
                    file_id += 1
                else:
                    print("REJECTED! file_id: ", file_id, " file_length: ", file_length, "num_block: ", num_block)
            elif stripped_line[0] == 'a':
                file_id_for_access = int(stripped_line.rsplit(':')[1])
                byte_offset = int(stripped_line.rsplit(':')[2])
                access(file_id_for_access, byte_offset)
            elif stripped_line[0] == 's':
                file_id_for_shrink = int(stripped_line.rsplit(':')[1])
                shrink_block = int(stripped_line.rsplit(':')[2])
                shrink_block = shrink(file_id_for_shrink, shrink_block)
                if shrink_block != -1:
                    block_number += shrink_block
                    print("SHRINKED! file_id: ", file_id, " file_length: ", file_length)
                else:
                    print("SHRINK REJECTED! file_id: ", file_id, " file_length: ", file_length)
            elif stripped_line[0] == 'e':
                file_id_for_extend = int(stripped_line.rsplit(':')[1])
                extension = int(stripped_line.rsplit(':')[2])
                if extension <= block_number:
                    extension_block = extend(file_id_for_extend, extension)
                    if extension_block != -1:
                        block_number -= extension_block
                        print("EXTENDED! file_id: ", file_id, " file_length: ", file_length)
                    else:
                        print("EXTENSION REJECTED! file_id: ", file_id, " file_length: ", file_length)
                # else:
                # print("CANNOT EXTEND, NO ENOUGH SPACE!")


if __name__ == "__main__":
    main()
    # print("FAT")
    # print(FAT)
    # print("DT")
    # print(DT)
    # print("Directory")
    # print(directory)
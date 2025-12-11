# Buat fungsi untuk memperoleh isi dari Stack terakhir
def getLastStack(stack):
    lastStack = []
    for i in range(len(stack) - 1, -1, -1):
        lastStack.append(stack[i])
    return lastStack

# Buat fungsi untuk memperoleh isi dari Queue
def getQueue(stack):
    queue = []
    while len(stack) > 0:
        queue.append(stack.pop())
    return queue

# Memasukkan data ke dalam stack
stack = [P, Q, R, S, T, U, V]

# Menghapus sebanyak 4 elemen dari stack
for i in range(4):
    stack.pop()

# Meng-insert elemen yang sudah dihapus ke Queue
queue = getQueue(stack)

# Menghapus 1 elemen dari Queue
queue.pop(0)

# Meng-insert elemen yang sudah dihapus ke Stack
stack.append(queue[0])

# Mencetak isi Stack terakhir
print("Isi Stack terakhir:", getLastStack(stack))

# Mencetak isi Queue
print("Isi Queue:", getQueue(stack))

import os,sys

def to_delete():
    for dirname, dirnames, filenames in os.walk('test'):
        # editing the 'dirnames' list will stop os.walk() from recursing into there.
        if '.git' in dirnames:
            # don't go into any .git directories.
            dirnames.remove('.git')

        # print path to all subdirectories first.
        for subdirname in dirnames:
            print(os.path.join(dirname, subdirname))

        # print path to all filenames.
        for filename in filenames:
            print(os.path.join(dirname, filename))


def direc_tree_ory(p,j):
    for i in os.listdir(str(p)):
        try:
            t=os.path.join(p,i)
            if os.path.isdir(t):
                
                print(j+'#'+i)
                direc_tree_ory(t,j+'-->')
                print ('')
            else:
                x=j+i
                print(x)
        except:
            print('\n**Exception. **\n')
        
k=''
s="./test/origin"
print('Path:' + s)
try:
    direc_tree_ory(s,k)
except:
    print('end of program')
    pass
# Direc-Tree
# Desc: A basic file traversal application scripted in Python 2.7.11 
# Authored by- Shivanjan Chakravorty
# Github- github.com/Glitchfix
# LinkedIn- linkedin.com/in/shivanjan-chakravorty
# Email- schakravorty846@gmail.com
# Phone- +91-96-58-965891
import os,sys

def direc_tree_ory(p,j):
    for i in os.listdir(str(p)):
        try:
            t=os.path.join(p,i)
            if os.path.isdir(t):
                
                print j+'#'+i
                direc_tree_ory(t,j+'-->')
                print ''
            else:
                x=j+i
                print x
        except:
            print '\n***AUTHORISED ELEVATION REQUIRED***\n'
        
k=''
s=raw_input('Which drive do you want to search? ').upper()
s+=":\\"
print 'Drive:',s
while True:
    #s=os.getcwd()
    try:
        direc_tree_ory(s,k)
    except:
        raw_input('\n\nPress enter to continue or restart\n the program in administrator mode')
        pass
import bcrypt
import time

def hashText(text, iters = 6):
    '''Returns a hash of the text using bcrypt for n iterations'''
    return bcrypt.hashpw(text, bcrypt.gensalt(iters))

def test(n):
    '''Test time for n bcrypt iterations'''
    start = time.time()
    h = hashText('teststring', n)
    print time.time()-start
    

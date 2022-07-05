# Binary search

Template for binary search prefer lower a lower bound. Copy-paste and edit solving more complex problems.
```python
def search(arr, v):    
    low, high = 0, len(arr)
    
    while low < high:
        mid = (low + high) // 2
        if arr[mid] == v:
            return mid
        
        if v < arr[mid]:
            high = mid
        else:
            low = mid + 1
            
    return -1
```
## Key points
* The choice of low/high/mid should **_ALWAYS_** shrink the bound
* Keep in mind what happens when there are "few" elements; 0, 1, 2 may cause problems
* This becomes plain old binary search if `FOUND=True` and `NOT_FOUND=False`.
* The initial range should include the entire bound of things you want to find
    For example, we can:
  * Index where we want to insert `v` into `arr` (which may be at the edges)

## Language-specific notes

### C/C++
* Iterators and size types outside their natural range.
* high + low overflow

### Python
Index -1.

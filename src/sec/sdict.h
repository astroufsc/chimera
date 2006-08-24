#ifndef _S_DICT_H_
#define _S_DICT_H_ 1

#include <stddef.h>

#include "dict.h"

#ifndef TRUE
#define TRUE 1
#endif

#ifndef FALSE
#define FALSE 0
#endif

typedef struct _SDict SDict;

struct _SDict {

  dict_t* priv;

};

typedef void (*s_dict_clbk)(SDict* dict, void* key, void* value, void* data);

SDict*	s_dict_new(void);
void	s_dict_free(SDict* dict);

int	s_dict_add(SDict* dict, const void* key, void* value);
int	s_dict_add_array(SDict* dict, const void* keys[], void* values[], int n);

int	s_dict_remove(SDict* dict, const void* key);

void*	s_dict_get(SDict* dict, const void* key);

int	s_dict_set(SDict* dict, const void* key, void* value);

int	s_dict_has(SDict* dict, const void* key);

int	s_dict_foreach(SDict* dict, void* data, s_dict_clbk clbk);

int	s_dict_count(SDict* dict);


#endif /* !_S_DICT_H */

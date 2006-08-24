#include "sdict.h"

#include <assert.h>
#include <stdlib.h>
#include <string.h>

static dnode_t* s_dict_get_node(SDict* dict, const void* key);

SDict*	s_dict_new(void) {

  SDict* dict = (SDict*)calloc(1, sizeof(SDict));

  assert(dict != NULL);

  dict->priv = dict_create(DICTCOUNT_T_MAX, strcmp);

  return dict;

}

void	s_dict_free(SDict* dict) {

  assert(dict != NULL);

  dict_free(dict->priv);
  dict_destroy(dict->priv);

  free(dict);

}

int	s_dict_add(SDict* dict, const void* key, void* value) {

  assert(dict != NULL);
  assert(key != NULL);
  assert(value != NULL);

  dnode_t* node = dnode_create(value);

  if(s_dict_has(dict, key))
    return FALSE;

  dict_insert(dict->priv, node, key);

  return TRUE;

}

int	s_dict_add_array(SDict* dict, const void* keys[], void* values[], int n) {

  assert(dict != NULL);
  assert(keys != NULL);
  assert(values != NULL);
  assert(n > 0);

  int i;

  for(i = 0; i < n; i++)
    s_dict_add(dict, keys[i], values[i]);
    
  return TRUE;

}

int	s_dict_remove(SDict* dict, const void* key) {

  assert(dict != NULL);
  assert(key != NULL);

  dnode_t* node = s_dict_get_node(dict, key);

  if(node != NULL) {
    
    dict_delete(dict->priv, node);

    dnode_destroy(node);

    return TRUE;

  } else {

    return FALSE;

  }

}

void*	s_dict_get(SDict* dict, const void* key) {

  assert(dict != NULL);
  assert(key != NULL);

  dnode_t* node = s_dict_get_node(dict, key);

  if(node != NULL) {
    return dnode_get(node);
  }else {
    return NULL;

  }

}

static dnode_t* s_dict_get_node(SDict* dict, const void* key) {

  assert(dict != NULL);
  assert(key != NULL);

  dnode_t* found = dict_lookup(dict->priv, key);

  return found;

}

int	s_dict_set(SDict* dict, const void* key, void* value) {

  assert(dict != NULL);
  assert(key != NULL);
  assert(value != NULL);

  dnode_t* node = s_dict_get_node(dict, key);

  if(node != NULL) {

    dnode_put(node, value);
    return TRUE;

  } else {

    return FALSE;

  }

}

int	s_dict_has(SDict* dict, const void* key) {

  assert(dict != NULL);
  assert(key != NULL);

  dnode_t* node = s_dict_get_node(dict, key);

  if(node != NULL) {

    return TRUE;

  } else {

    return FALSE;

  }

}

int	s_dict_foreach(SDict* dict, void* data, s_dict_clbk clbk) {

  return TRUE;

}

int	s_dict_count(SDict* dict) {

  assert(dict != NULL);

  return (int)dict_count(dict->priv);

}

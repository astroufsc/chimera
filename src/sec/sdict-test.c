#include "sdict.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void) {

  SDict* dict = s_dict_new();
  assert(dict != NULL);

  int i = s_dict_count(dict);
  assert(i == 0);

  s_dict_add(dict, "NOME", "VALOR");

  int j = s_dict_count(dict);
  assert(j == 1);

  char* s = (char*) s_dict_get(dict, "NOME");;
  assert(strcmp("VALOR", s) == 0);;

  char* keys[4] = {"NOME1", "NOME2", "NOME3", "NOME4"};
  char* values[4] = {"VALOR1", "VALOR2", "VALOR3", "VALOR4"};

  s_dict_add_array(dict, keys, values, 4);

  char* s1 = (char*) s_dict_get(dict, "NOME1");;
  assert(strcmp("VALOR1", s1) == 0);;

  char* s2 = (char*) s_dict_get(dict, "NOME2");;
  assert(strcmp("VALOR2", s2) == 0);;

  char* s3 = (char*) s_dict_get(dict, "NOME3");;
  assert(strcmp("VALOR3", s3) == 0);;

  char* s4 = (char*) s_dict_get(dict, "NOME4");;
  assert(strcmp("VALOR4", s4) == 0);;

  s_dict_set(dict, "NOME4", "NOVO");

  char* s5 = (char*) s_dict_get(dict, "NOME4");;
  assert(strcmp("NOVO", s5) == 0);;

  assert(s_dict_has(dict, "NOME4"));

  s_dict_remove(dict, "NOME4");
  
  assert(! s_dict_has(dict, "NOME4"));

  s_dict_free(dict);
  assert(dict != NULL);

  return 0;

}

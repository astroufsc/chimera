/* -*- C -*-  (not really, but good for syntax highlighting) */
%{
#ifndef SWIG_FILE_WITH_INIT
#  define NO_IMPORT_ARRAY
#endif
#include "stdio.h"
#include <numpy/arrayobject.h>

/* The following code originally appeared in enthought/kiva/agg/src/numeric.i,
 * author unknown.  It was translated from C++ to C by John Hunter.  Bill
 * Spotz has modified it slightly to fix some minor bugs, add some comments
 * and some functionality.
 */

/* Macros to extract array attributes.
 */
#define is_array(a)            ((a) && PyArray_Check((PyArrayObject *)a))
#define array_type(a)          (int)(PyArray_TYPE(a))
#define array_dimensions(a)    (((PyArrayObject *)a)->nd)
#define array_size(a,i)        (((PyArrayObject *)a)->dimensions[i])
#define array_is_contiguous(a) (PyArray_ISCONTIGUOUS(a))

/* Given a PyObject, return a string describing its type.
 */
char* pytype_string(PyObject* py_obj) {
  if (py_obj == NULL          ) return "C NULL value";
  if (PyCallable_Check(py_obj)) return "callable"    ;
  if (PyString_Check(  py_obj)) return "string"      ;
  if (PyInt_Check(     py_obj)) return "int"         ;
  if (PyFloat_Check(   py_obj)) return "float"       ;
  if (PyDict_Check(    py_obj)) return "dict"        ;
  if (PyList_Check(    py_obj)) return "list"        ;
  if (PyTuple_Check(   py_obj)) return "tuple"       ;
  if (PyFile_Check(    py_obj)) return "file"        ;
  if (PyModule_Check(  py_obj)) return "module"      ;
  if (PyInstance_Check(py_obj)) return "instance"    ;

  return "unkown type";
}

/* Given a Numeric typecode, return a string describing the type.
 */
char* typecode_string(int typecode) {
  char* type_names[20] = {"char","unsigned byte","byte","short",
			  "unsigned short","int","unsigned int","long",
			  "float","double","complex float","complex double",
			  "object","ntype","unkown"};
  return type_names[typecode];
}

/* Make sure input has correct numeric type.  Allow character and byte
 * to match.  Also allow int and long to match.
 */
int type_match(int actual_type, int desired_type) {
  return PyArray_EquivTypenums(actual_type, desired_type);
}

/* Given a PyObject pointer, cast it to a PyArrayObject pointer if
 * legal.  If not, set the python error string appropriately and
 * return NULL./
 */
PyArrayObject* obj_to_array_no_conversion(PyObject* input, int typecode) {
  PyArrayObject* ary = NULL;
  if (is_array(input) && (typecode == PyArray_NOTYPE || 
			  PyArray_EquivTypenums(array_type(input), 
						typecode))) {
        ary = (PyArrayObject*) input;
    }
    else if is_array(input) {
      char* desired_type = typecode_string(typecode);
      char* actual_type = typecode_string(array_type(input));
      PyErr_Format(PyExc_TypeError, 
		   "Array of type '%s' required.  Array of type '%s' given", 
		   desired_type, actual_type);
      ary = NULL;
    }
    else {
      char * desired_type = typecode_string(typecode);
      char * actual_type = pytype_string(input);
      PyErr_Format(PyExc_TypeError, 
		   "Array of type '%s' required.  A %s was given", 
		   desired_type, actual_type);
      ary = NULL;
    }
  return ary;
}

/* Convert the given PyObject to a Numeric array with the given
 * typecode.  On Success, return a valid PyArrayObject* with the
 * correct type.  On failure, the python error string will be set and
 * the routine returns NULL.
 */
PyArrayObject* obj_to_array_allow_conversion(PyObject* input, int typecode,
                                             int* is_new_object)
{
  PyArrayObject* ary = NULL;
  PyObject* py_obj;
  if (is_array(input) && (typecode == PyArray_NOTYPE || type_match(array_type(input),typecode))) {
    ary = (PyArrayObject*) input;
    *is_new_object = 0;
  }
  else {
    py_obj = PyArray_FromObject(input, typecode, 0, 0);
    /* If NULL, PyArray_FromObject will have set python error value.*/
    ary = (PyArrayObject*) py_obj;
    *is_new_object = 1;
  }
  return ary;
}

/* Given a PyArrayObject, check to see if it is contiguous.  If so,
 * return the input pointer and flag it as not a new object.  If it is
 * not contiguous, create a new PyArrayObject using the original data,
 * flag it as a new object and return the pointer.
 */
PyArrayObject* make_contiguous(PyArrayObject* ary, int* is_new_object,
                               int min_dims, int max_dims)
{
  PyArrayObject* result;
  if (array_is_contiguous(ary)) {
    result = ary;
    *is_new_object = 0;
  }
  else {
    result = (PyArrayObject*) PyArray_ContiguousFromObject((PyObject*)ary, 
							   array_type(ary), 
							   min_dims,
							   max_dims);
    *is_new_object = 1;
  }
  return result;
}

/* Convert a given PyObject to a contiguous PyArrayObject of the
 * specified type.  If the input object is not a contiguous
 * PyArrayObject, a new one will be created and the new object flag
 * will be set.
 */
PyArrayObject* obj_to_array_contiguous_allow_conversion(PyObject* input,
                                                        int typecode,
                                                        int* is_new_object) {
  int is_new1 = 0;
  int is_new2 = 0;
  PyArrayObject* ary2;
  PyArrayObject* ary1 = obj_to_array_allow_conversion(input, typecode, 
						      &is_new1);
  if (ary1) {
    ary2 = make_contiguous(ary1, &is_new2, 0, 0);
    if ( is_new1 && is_new2) {
      Py_DECREF(ary1);
    }
    ary1 = ary2;    
  }
  *is_new_object = is_new1 || is_new2;
  return ary1;
}

/* Test whether a python object is contiguous.  If array is
 * contiguous, return 1.  Otherwise, set the python error string and
 * return 0.
 */
int require_contiguous(PyArrayObject* ary) {
  int contiguous = 1;
  if (!array_is_contiguous(ary)) {
    PyErr_SetString(PyExc_TypeError, "Array must be contiguous.  A discontiguous array was given");
    contiguous = 0;
  }
  return contiguous;
}

/* Require the given PyArrayObject to have a specified number of
 * dimensions.  If the array has the specified number of dimensions,
 * return 1.  Otherwise, set the python error string and return 0.
 */
int require_dimensions(PyArrayObject* ary, int exact_dimensions) {
  int success = 1;
  if (array_dimensions(ary) != exact_dimensions) {
    PyErr_Format(PyExc_TypeError, 
		 "Array must be have %d dimensions.  Given array has %d dimensions", 
		 exact_dimensions, array_dimensions(ary));
    success = 0;
  }
  return success;
}

/* Require the given PyArrayObject to have one of a list of specified
 * number of dimensions.  If the array has one of the specified number
 * of dimensions, return 1.  Otherwise, set the python error string
 * and return 0.
 */
int require_dimensions_n(PyArrayObject* ary, int* exact_dimensions, int n) {
  int success = 0;
  int i;
  char dims_str[255] = "";
  char s[255];
  for (i = 0; i < n && !success; i++) {
    if (array_dimensions(ary) == exact_dimensions[i]) {
      success = 1;
    }
  }
  if (!success) {
    for (i = 0; i < n-1; i++) {
      sprintf(s, "%d, ", exact_dimensions[i]);                
      strcat(dims_str,s);
    }
    sprintf(s, " or %d", exact_dimensions[n-1]);            
    strcat(dims_str,s);
    PyErr_Format(PyExc_TypeError, 
		 "Array must be have %s dimensions.  Given array has %d dimensions",
		 dims_str, array_dimensions(ary));
  }
  return success;
}    

/* Require the given PyArrayObject to have a specified shape.  If the
 * array has the specified shape, return 1.  Otherwise, set the python
 * error string and return 0.
 */
int require_size(PyArrayObject* ary, int* size, int n) {
  int i;
  int success = 1;
  int len;
  char desired_dims[255] = "[";
  char s[255];
  char actual_dims[255] = "[";
  for(i=0; i < n;i++) {
    if (size[i] != -1 &&  size[i] != array_size(ary,i)) {
      success = 0;    
    }
  }
  if (!success) {
    for (i = 0; i < n; i++) {
      if (size[i] == -1) {
	sprintf(s, "*,");                
      }
      else
      {
	sprintf(s, "%d,", size[i]);                
      }    
      strcat(desired_dims,s);
    }
    len = strlen(desired_dims);
    desired_dims[len-1] = ']';
    for (i = 0; i < n; i++) {
      sprintf(s, "%d,", array_size(ary,i));                            
      strcat(actual_dims,s);
    }
    len = strlen(actual_dims);
    actual_dims[len-1] = ']';
    PyErr_Format(PyExc_TypeError, 
		 "Array must be have shape of %s.  Given array has shape of %s",
		 desired_dims, actual_dims);
  }
  return success;
}
/* End John Hunter translation (with modifications by Bill Spotz) */

%}

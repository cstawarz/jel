JSON Expression Language (JEL)
==============================



Identifiers
-----------

Identifiers are case sensitive and consist of a letter (A-Z, a-z) or underscore followed by zero or more letters, digits (0-9), and/or underscores.



Values
------

Every valid JSON document is a valid JEL expression (i.e. JEL is a proper superset of JSON).  JEL supports the same data types as JSON, using the same literal syntax, with the following additions:

* Number literals can include an alphanumeric suffix ("tag"), which can be any valid identifier.  Interpretation of the suffix is up to the implementation.  (One possible use is to specify the unit of a value.)

* String literals can be enclosed in single or double quotes.  Python-style multiline string literals are also supported.

* Value lists in array literals and member lists in object literals can have an extra comma at the end, provided that the list is not empty.

Strings are Unicode.

Objects are sets of key/value pairs (i.e. associative arrays), where the key is a string and the value can be anything.  As in JavaScript, if a key is a valid identifier, then the quotes around it may be omitted within an object literal.  Because of this, key names in object literals must always be literal strings or identifiers (i.e. they can't be arbitrary expressions as in Python).

All values are immutable.



Operators
---------

From highest to lowest precedence:

```
(expression)                       Subexpression
x[index], x(args...), x.name       Indexing, call, attribute access
**                                 Exponentiation
+x, -x                             Positive, negative
*, /, %                            Multiplication, division, remainder
+, -                               Addition, subtraction
<, <=, >, >=, !=, ==, in, not in   Comparisons
not x                              Logical NOT
and                                Logical AND
or                                 Logical OR
```

Logical operators always return a boolean value (i.e. true or false).  Every data type has a truth value and can be used as an operand to a logical operator.  (TODO:  Do we follow Lua or Python's approach to the truthiness of values?)

Comparison operators are chained as in Python.  That is, `x < y < z` is equivalent to `(x < y) and (y < z)`.  The result of a comparision chain is always a boolean.

Every data type can be tested for (in)equality with any other data type.  Values of different types always compare not equal.  However, ordering comparisons are *not* valid between different data types.

As in Python, exponentiation groups from right to left.  That is, 2**3**4 is equivalent to 2**(3**4), not (2**3)**4.

Only objects support attribute access, and only for keys that are valid identifiers.  For example, if object o has key 'abc123', then o.abc123 is equivalent to o['abc123'].

JEL doesn't currently support C-style bitwise operators (|, ^, &, <<, >>), but it might in the future.  Since C-style AND and OR (&&, ||) are easily confused with bitwise AND and OR (&, |), JEL eschews the former and instead adopts Python-style 'and' and 'or'.

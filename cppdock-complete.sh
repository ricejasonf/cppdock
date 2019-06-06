#!/usr/bin/env bash

_cppdock_complete()
{

  ITEMS=(cppdock _complete "${COMP_LINE}")
  COMPREPLY=($("${ITEMS[@]}"))
}

complete -F _cppdock_complete cppdock

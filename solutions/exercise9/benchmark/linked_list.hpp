#pragma once
#include <cstddef>

template<class T>
class LinkedListNode
{
public:
  LinkedListNode* next = nullptr;
  T value;
};

template<class T>
class LinkedList
{
public:
  class iterator
  {
    friend class LinkedList;

  public:
    iterator(LinkedListNode<T>* ptr);
    T& operator*();
    iterator& operator++();
    iterator operator+(unsigned int n);
    bool operator!=(const iterator& other);

  private:
    LinkedListNode<T>* ptr;
  };

  iterator begin();
  iterator end();

  T& operator[](size_t pos);

  size_t size();

  iterator insert(iterator pos, const T& value);
  iterator erase(iterator pos);

  // void shuffle_list(int);

private:
  LinkedListNode<T>* head = nullptr;
  size_t __size = 0;
};

#include "linked_list_impl.hpp"

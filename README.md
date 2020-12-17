# Caching

### Stateful operations

Suppose we have a simple class representing a machine learning model.

```python
class Model:
    
    def learn(self, dataset):
        pass
    
    def predict(self, inputs):
        pass
```

The `learn()` method causes the model to train on a dataset, and the `predict()` method asks the model, whatever state it's in, to predict the outputs for a vector of inputs. Now what if we want to cache the results of `predict()`? If we call a model that's in the same state with the same inputs, the prediction should be the same, so we can cache  that. It's easy to check if we've seen the inputs before, but how do we know what state the model is in?

At first this seems easy. The caching framework can just check the `self` variable. If it's in the same state, use the cached result. The state of a model is determined by, say, two fields:

- What dataset the model was trained on.
- Some information about the model's initial state, say a random seed.

With these two pieces of information, we can tell if, when given the same input vector, the model will make the same prediction.

To see why this doesn't work, imagine the code you would write to make use of this class. It would just look something like this:

```python
model.learn(data)
result = model.predict(inputs)
```

Here's the problem. What happens when you call `learn()`? The model can't *actually* run the training algorithm, because it doesn't have enough information to know if it needs to yet. It should only do the training if `inputs`, one line later, is something it hasn't seen before.

The easy way to do this is like this:

```python
class Model:
    
    def learn(self, dataset):
        self.dataset = dataset
        self.trained = False
    
    def predict(self, inputs):
        if not self.trained:
            # do training
```

This works, but if we do a lot of stateful operations we have to keep track of those, the order they happened in, and what arguments were passed. We have to pollute our class with all kinds of variables just to keep track of this accumulated state. How can we build a general caching mechanism to track this kind of thing for us?

### Stateful cachable classes

Not every function is cachable. In order for a function to be cachable, it needs to be *pure*, and depend only on its arguments (or the cache needs to be made aware of what ambient state the function depends on, in which case those elements essentially become implicit arguments anyway, since you'll have to type them up explicitly in a list somewhere just like arguments).

Similarly, a class needs to satisfy certain constraints in order to be cachable: it needs to be what I'll call a *pure class*.

> **Definiton.** A *pure class* is one which satisfies the following constraints:
>
> - The return value of any method should depend only on the values of the attributes of the class an the method arguments.
> - The attributes of a class should only be changed when a class method is called (including the constructor).
> - The manner in which a class attribute changes when a method is called should be a pure function of the current values of the attributes of the class, and the method arguments.

This is basically the classical OOP conception of a class. The class is effectively just a box that remembers what methods you called, in what order, and with what arguments.

Given a pure class, we can easily do caching by simply keeping track of what stateful methods got called, and building a history. When we call a cached method, we then, and only then, run the entire history of stateful methods, *if necessary*.
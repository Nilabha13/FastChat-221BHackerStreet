$N$ (hyperparameter) clients, $M$ servers<br>
$N \in \{5,10,\ldots,100\}$

1. ExponentialTimeDelay: Consider the following process: We choose a two clients uniformly at random from set of all clients. We make one of them send a message to the other. This process is repeated $K$ times, with the time difference between two consecutive such events modelled by an exponential random variable with mean $\mu$ (hyperparameter).
2. IOnlyTalkToBestie: Pick a client at random. Choose a number following a discrete Gaussian with mean $\mu$ (hyperparameter) and standard deviation $\sigma$ - this represents the number of other clients this client talks to. Choose that number of other clients from the remaining pool uniformly at random. The OG client sends a message to all of them. This process is repeated $K$ times sequentially with a time difference $\delta t$.
3. FixedImageRatio: Each client has a probability $p$ (hyperparameter) of sending an image instead of a message. Integrate this pattern in all the above patterns.

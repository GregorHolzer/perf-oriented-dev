#include <stdio.h>
#include <stdlib.h>

#ifndef S
#define S 1000
#endif
#define N S
#define M S
#define K S

#ifndef M_T
#define M_T 256
#endif
#ifndef N_T
#define N_T 256
#endif
#ifndef K_T
#define K_T 256
#endif

#define MIN(X, Y) ((X) < (Y) ? (X) : (Y))
#define MAX(X, Y) ((X) > (Y) ? (X) : (Y))

#define TYPE double
#define MATRIX TYPE **

MATRIX createMatrix(unsigned x, unsigned y)
{
	TYPE *data = calloc(x * y, sizeof(TYPE));

	TYPE **index = malloc(x * sizeof(TYPE *));
	index[0] = data;
	for (unsigned i = 1; i < x; ++i)
	{
		index[i] = &(data[i * y]);
	}
	return index;
}

void freeMatrix(MATRIX matrix)
{
	free(matrix[0]);
	free(matrix);
}

int main(void)
{
	// create the matrices
	MATRIX A = createMatrix(N, M);
	MATRIX B = createMatrix(M, K);
	MATRIX C = createMatrix(N, K);

	// initialize the matrices

	// A contains real values
	for (int i = 0; i < N; i++)
	{
		for (int j = 0; j < M; j++)
		{
			A[i][j] = i * j;
		}
	}

	// B is the identity matrix
	for (int i = 0; i < M; i++)
	{
		for (int j = 0; j < K; j++)
		{
			B[i][j] = (i == j) ? 1 : 0;
		}
	}

	for (int m_tile = 0; m_tile < M; m_tile += M_T)
	{
		for (int n_tile = 0; n_tile < N; n_tile += N_T)
		{
			for (int k_tile = 0; k_tile < K; k_tile += K_T)
			{
				for (int m = m_tile; m < MIN(M, m_tile + M_T); ++m)
				{
					for (int n = n_tile; n < MIN(N, n_tile + N_T); ++n)
					{
						for (int k = k_tile; k < MIN(K, k_tile + K_T); ++k)
						{
							C[m][k] += A[m][n] * B[n][k];
						}
					}
				}
			}
		}
	}

	// verify result
	int success = 1;
	for (int i = 0; i < N; i++)
	{
		for (int j = 0; j < MIN(M, K); j++)
		{
			if (A[i][j] != C[i][j])
			{
				success = 0;
			}
		}
		for (int j = MIN(M, K); j < MAX(M, K); j++)
		{
			if (C[i][j] != 0)
			{
				success = 0;
			}
		}
	}

	// print verification result
	printf("Verification: %s\n", (success) ? "OK" : "ERR");

	freeMatrix(A);
	freeMatrix(B);
	freeMatrix(C);

	return success ? EXIT_SUCCESS : EXIT_FAILURE;
}

#' ---
#' title: Wrapper for ocp package in TCPDBench (modified with future averaging logic)
#' ---

library(argparse)
library(ocp)

load.utils <- function() {
    cmd.args <- commandArgs(trailingOnly=F)
    file.arg <- "--file="
    this.script <- sub(file.arg, "", cmd.args[grep(file.arg, cmd.args)])
    this.dir <- dirname(this.script)
    utils.script <- file.path(this.dir, 'utils.R')
    source(utils.script)
}

parse.args <- function() {
    parser <- ArgumentParser(description='Wrapper for ocp package with future averaging')
    parser$add_argument('-i','--input',help='path to the input data file',required=TRUE)
    parser$add_argument('-o','--output',help='path to the output file')
    parser$add_argument('-l','--lambda',help='lambda parameter for constant hazard function',type='integer',default=100)
    parser$add_argument('--prior-a',help='Prior alpha for student-t',type='double',default=1)
    parser$add_argument('--prior-b',help='Prior beta for student-t',type='double',default=1)
    parser$add_argument('--prior-k',help='Prior kappa for student-t',type='double',default=1)
    parser$add_argument('--lookahead',
                        help='number of future points to average for detection',
                        type='integer',
                        default=12)
    return(parser$parse_args())
}

main <- function()
{
    args <- parse.args()
    data <- load.dataset(args$input)

    defaults <- list(missPts="none",
                     cpthreshold=0.5,
                     truncRlim=10^(-4),
                     minRlength=1,
                     maxRlength=10^4,
                     minsep=1,
                     maxsep=10^4)
    defaults$multivariate = data$original$n_dim > 1
    params <- make.param.list(args, defaults)

    hazard_func <- function(x, lambda) {
        const_hazard(x, lambda=params$lambda)
    }

    model.params <- list(list(m=0, k=params$prior_k, a=params$prior_a, b=params$prior_b))

    start.time <- Sys.time()
    result <- tryCatch({
        n <- nrow(data$mat)
        ocp_instance <- NULL
        detected_cps <- c()

        for (i in seq_len(n)) {
            # build artificial point as avg of next x
            if (i < n) {
                end_idx <- min(n, i + args$lookahead)
                future_segment <- data$mat[(i+1):end_idx,,drop=FALSE]
                avg_future <- colMeans(future_segment)
                artificial_point <- matrix(avg_future, nrow=1)

                # run detection using artificial point
                tmp <- NULL
                capture.output({
                    tmp <- onlineCPD(artificial_point, oCPD=ocp_instance,
                                     missPts=params$missPts,
                                     hazard_func=hazard_func,
                                     probModel=list("gaussian"),
                                     init_params=model.params,
                                     multivariate=params$multivariate,
                                     cpthreshold=params$cpthreshold,
                                     truncRlim=params$truncRlim,
                                     minRlength=params$minRlength,
                                     maxRlength=params$maxRlength,
                                     minsep=params$minsep,
                                     maxsep=params$maxsep)
                }, file='/dev/null')

                # check if tmp reports a CP at this step
                if (length(tmp$changepoint_lists$maxCPs[[1]]) > 0) {
                    last_cp <- tail(tmp$changepoint_lists$maxCPs[[1]], 1)
                    if (last_cp == i) {
                        detected_cps <- c(detected_cps, i)
                    }
                }
            }

            # update ocp_instance with the *real* point
            real_point <- matrix(data$mat[i,], nrow=1)
            capture.output({
                ocp_instance <- onlineCPD(real_point, oCPD=ocp_instance,
                                          missPts=params$missPts,
                                          hazard_func=hazard_func,
                                          probModel=list("gaussian"),
                                          init_params=model.params,
                                          multivariate=params$multivariate,
                                          cpthreshold=params$cpthreshold,
                                          truncRlim=params$truncRlim,
                                          minRlength=params$minRlength,
                                          maxRlength=params$maxRlength,
                                          minsep=params$minsep,
                                          maxsep=params$maxsep)
            }, file='/dev/null')
        }

        list(locations=detected_cps, error=NULL)
    }, error=function(e) {
        return(list(locations=NULL, error=e$message))
    })
    stop.time <- Sys.time()
    runtime <- difftime(stop.time, start.time, units="secs")

    if (!is.null(result$error))
        exit.with.error(data$original, args, params, result$error)

    # convert to 0-based
    locations <- as.list(result$locations - 1)
    exit.success(data$original, args, params, locations, runtime)
}

load.utils()
main()

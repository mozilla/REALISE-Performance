#' ---
#' title: Wrapper for ecp package in TCPDBench
#' author: G.J.J. van den Burg
#' date: 2019-09-29
#' license: See LICENSE file.
#' copyright: 2019, The Alan Turing Institute
#' ---

library(argparse)
library(ecp)

load.utils <- function() {
    # get the name of the current script so we can load utils.R (yay, R!)
    cmd.args <- commandArgs(trailingOnly=F)
    file.arg <- "--file="
    this.script <- sub(file.arg, "", cmd.args[grep(file.arg, cmd.args)])
    this.dir <- dirname(this.script)
    utils.script <- file.path(this.dir, 'utils.R')
    source(utils.script)
}

parse.args <- function() {
    parser <- ArgumentParser(description='Wrapper for ecp package')
    parser$add_argument('-i', 
                        '--input',
                        help='path to the input data file',
                        required=TRUE
    )
    parser$add_argument('-o',
                        '--output',
                        help='path to the output file'
    ) 
    parser$add_argument('-a',
                        '--algorithm',
                        help='algorithm to use',
                        choices=c('e.agglo', 'e.divisive'),
                        required=TRUE
    )
    parser$add_argument('--alpha',
                        type='double',
                        help='alpha parameter for e.agglo and e.divisive')
    parser$add_argument('--minsize',
                        help='minsize argument for e.divisive',
                        type='integer', default=30)
    parser$add_argument('-R', '--runs',
                        help='number of random permutations to use for e.divisive',
                        type='integer', default=199)
    parser$add_argument('--siglvl',
                        type='double',
                        help='Significance level to use for tests')
    return(parser$parse_args())
}

main <- function() {
    args <- parse.args()
    raw_args <- args

    # load the dataset
    data <- load.dataset(args$input)

    start.time <- Sys.time()
    result <- tryCatch({
        if (args$algorithm == 'e.agglo') {
            out <- e.agglo(data$mat, alpha=args$alpha)
            locs <- out$estimates
        } else if (args$algorithm == 'e.divisive') {
            out <- e.divisive(data$mat, sig.lvl=args$siglvl, R=args$runs,
                              min.size=args$minsize, alpha=args$alpha)
            locs <- out$estimates
        }
        list(locations=locs, error=NULL)
    }, error=function(e) {
        return(list(locations=NULL, error=e$message))
    })

    stop.time <- Sys.time()
    runtime <- difftime(stop.time, start.time, units='secs')

    if (!is.null(result$error))
        exit.with.error(data$original, raw_args, args, result$error)

    # convert to 0-based indices
    locations <- as.list(result$locations - 1)

    exit.success(data$original, raw_args, args, locations, runtime)
}

load.utils()
main()
